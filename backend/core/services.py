from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from django.db import transaction
from .models import (
    VehicleType, ServiceTier, CustomerSegment, 
    ValueAddedService, City, Route, PricingQuote
)

class PricingError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class PricingEngine:
    """
    Core pricing engine implementing the DPYMA (Dynamic Pricing and Yield Management Algorithm).
    """

    def _to_d(self, val) -> Decimal:
        if val is None:
            return Decimal('0.00')
        return Decimal(str(val))

    RDS_WEIGHTS = {
        "terrain_grade": Decimal('2.0'),
        "road_surface_quality": Decimal('1.5'),
        "traffic_congestion": Decimal('1.0'),
        "weather_risk": Decimal('1.5'),
        "toll_gate_density": Decimal('0.5'),
        "historical_accident_rate": Decimal('1.0'),
        "border_checkpoint_freq": Decimal('1.0'),
    }

    DENSITY_FACTORS = {
        'metro': Decimal('1.15'),
        'tier_1': Decimal('1.05'),
        'tier_2': Decimal('1.00'),
        'tier_3': Decimal('0.95'),
        'semi_urban': Decimal('0.90'),
        'rural': Decimal('0.85'),
    }

    DEADHEAD_MULTIPLIERS = {
        'highly_balanced': Decimal('1.0'),
        'moderately_balanced': Decimal('1.1'),
        'unbalanced_origin_heavy': Decimal('1.3'),
        'seasonal': Decimal('1.4'),
        'remote_low_demand': Decimal('1.5'),
    }

    INSURANCE_RATES = {
        "basic": Decimal('0.0'),
        "standard": Decimal('0.5'),
        "premium": Decimal('1.0'),
        "comprehensive": Decimal('1.8'),
    }

    def _calculate_rds(self, route: Route) -> Decimal:
        total_weight = sum(self.RDS_WEIGHTS.values())
        raw_score = (
            self._to_d(route.terrain_grade) * self.RDS_WEIGHTS["terrain_grade"] +
            self._to_d(route.road_surface_quality) * self.RDS_WEIGHTS["road_surface_quality"] +
            self._to_d(route.traffic_congestion) * self.RDS_WEIGHTS["traffic_congestion"] +
            self._to_d(route.weather_risk) * self.RDS_WEIGHTS["weather_risk"] +
            self._to_d(route.toll_gate_density) * self.RDS_WEIGHTS["toll_gate_density"] +
            self._to_d(route.historical_accident_rate) * self.RDS_WEIGHTS["historical_accident_rate"] +
            self._to_d(route.border_checkpoint_freq) * self.RDS_WEIGHTS["border_checkpoint_freq"]
        )
        return (raw_score / (Decimal('10.0') * total_weight)) * Decimal('100.0')

    def _get_rds_surcharge_pct(self, score: Decimal) -> Decimal:
        if score < 20: return Decimal('0.0')
        if score < 40: return Decimal('5.0')
        if score < 60: return Decimal('10.0')
        if score < 80: return Decimal('15.0')
        return Decimal('25.0')

    @transaction.atomic
    def calculate_quote(self, 
                        user,
                        origin_name: str, 
                        destination_name: str, 
                        vehicle_code: str, 
                        cargo_weight: float, 
                        cargo_volume: float, 
                        service_tier_code: str, 
                        customer_segment_code: str, 
                        vas_codes: List[str],
                        insurance_tier: str,
                        declared_value: float,
                        loading_unloading_cost: float,
                        demand_multiplier: float = 1.0) -> PricingQuote:
        
        # 1. Fetch Master Data
        origin = City.objects.get(name=origin_name)
        destination = City.objects.get(name=destination_name)
        vehicle = VehicleType.objects.get(code=vehicle_code)
        service_tier = ServiceTier.objects.get(code=service_tier_code)
        segment = CustomerSegment.objects.get(code=customer_segment_code)
        route = Route.objects.get(origin_city=origin, dest_city=destination)
        
        # 2. Chargeable weight
        volumetric_weight = (Decimal(str(cargo_volume)) / Decimal('1.6667'))
        chargeable_weight = max(Decimal(str(cargo_weight)), volumetric_weight)
        
        # 3. Base Costs
        fuel_cost = (self._to_d(origin.fuel_price) / self._to_d(vehicle.fuel_efficiency_kmpl)) * self._to_d(route.distance_km)
        toll_cost = self._to_d(vehicle.toll_rate_per_km) * self._to_d(route.distance_km)
        
        # Amortization
        monthly_km = self._to_d(vehicle.estimated_annual_km) / Decimal('12.0')
        trip_fraction = self._to_d(route.distance_km) / monthly_km
        
        driver_cost = (self._to_d(vehicle.driver_salary_annual) / Decimal('12.0')) * trip_fraction
        depreciation = (self._to_d(vehicle.depreciation_annual) / Decimal('12.0')) * trip_fraction
        veh_insurance = (self._to_d(vehicle.insurance_annual) / Decimal('12.0')) * trip_fraction
        permit_cost = (self._to_d(vehicle.permit_fees_annual) / Decimal('12.0')) * trip_fraction
        maintenance = (self._to_d(vehicle.maintenance_per_km) + self._to_d(vehicle.tire_cost_per_km)) * self._to_d(route.distance_km)
        
        total_base_cost = (
            fuel_cost + toll_cost + driver_cost + depreciation + 
            veh_insurance + permit_cost + maintenance + self._to_d(loading_unloading_cost)
        )
        
        # 4. Multipliers
        # RDS
        rds_score = self._calculate_rds(route).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        rds_surcharge_pct = self._get_rds_surcharge_pct(rds_score)
        rds_surcharge_amount = total_base_cost * (rds_surcharge_pct / Decimal('100.0'))
        
        # M_density
        m_density = (self.DENSITY_FACTORS[origin.tier] + self.DENSITY_FACTORS[destination.tier]) / Decimal('2.0')
        
        # M_tier (Lane Viability)
        m_tier = self.DEADHEAD_MULTIPLIERS[route.lane_viability]
        
        # Chain Calculation
        # Step A: Base + RDS
        after_rds = total_base_cost + rds_surcharge_amount
        # Step B: Apply Density, Service Tier, Demand, and Lane Viability
        final_before_discount = (
            after_rds * 
            m_density * 
            self._to_d(service_tier.multiplier) * 
            self._to_d(demand_multiplier) * 
            m_tier
        )
        
        # 5. Customer Discount
        discount_amount = final_before_discount * (self._to_d(segment.discount_percentage) / Decimal('100.0'))
        after_discount = final_before_discount - discount_amount
        
        # 6. VAS
        vas_total = Decimal('0.00')
        vas_details = []
        active_vas = ValueAddedService.objects.filter(code__in=vas_codes, is_active=True)
        for vas in active_vas:
            v_price = self._to_d(vas.base_price)
            vas_total += v_price
            vas_details.append({"code": vas.code, "name": vas.name, "price": float(v_price)})
            
        # 7. Platform Fee & Insurance
        platform_fee = (after_discount + vas_total) * (self._to_d(segment.platform_fee_percentage) / Decimal('100.0'))
        ins_rate = self.INSURANCE_RATES.get(insurance_tier, Decimal('0.0'))
        insurance_premium = (self._to_d(declared_value) * ins_rate) / Decimal('100.0')
        
        # 8. Totals
        subtotal = after_discount + vas_total + platform_fee + insurance_premium
        gst = subtotal * Decimal('0.18')
        final_total = (subtotal + gst).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 9. Build Breakdown
        breakdown = {
            "origin": origin.name,
            "destination": destination.name,
            "distance": float(self._to_d(route.distance_km)),
            "vehicle": vehicle.display_name,
            "base_costs": {
                "fuel": float(fuel_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "toll": float(toll_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "fixed_amortized": float((driver_cost + depreciation + veh_insurance + permit_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "maintenance": float(maintenance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "total_base": float(total_base_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            },
            "multipliers": {
                "rds_score": float(rds_score),
                "rds_surcharge_pct": float(rds_surcharge_pct),
                "m_density": float(m_density.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)),
                "m_service": float(self._to_d(service_tier.multiplier)),
                "m_demand": float(self._to_d(demand_multiplier)),
                "m_tier": float(m_tier)
            },
            "adjustments": {
                "discount": float(discount_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "vas_total": float(vas_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "platform_fee": float(platform_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "insurance": float(insurance_premium.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            },
            "tax": {"gst": float(gst.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))},
            "final_total": float(final_total)
        }
        
        # 10. Save and Return
        quote = PricingQuote.objects.create(
            quote_id=f"QT-{uuid.uuid4().hex[:8].upper()}",
            owner=user,
            origin_city=origin.name,
            destination_city=destination.name,
            vehicle_type=vehicle,
            cargo_weight_tons=cargo_weight,
            cargo_volume_cbm=cargo_volume,
            service_tier=service_tier,
            customer_segment=segment,
            final_total=final_total,
            breakdown=breakdown
        )
        return quote
