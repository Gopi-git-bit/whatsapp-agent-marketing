from django.core.management.base import BaseCommand
from core.models import VehicleType, ServiceTier, CustomerSegment, ValueAddedService, City, Route

class Command(BaseCommand):
    help = 'Seed initial pricing data'

    def handle(self, *args, **options):
        # 1. Vehicle Types
        vehicles = [
            {
                "code": "mini_truck",
                "display_name": "Mini Truck (0.5-2T)",
                "fuel_efficiency_kmpl": 13.0,
                "toll_rate_per_km": 0.50,
                "capacity_tons": 2.0,
                "capacity_cbm": 10.0,
                "depreciation_annual": 120000,
                "insurance_annual": 20000,
                "driver_salary_annual": 240000,
                "permit_fees_annual": 10000,
                "maintenance_per_km": 2.0,
                "tire_cost_per_km": 0.8,
                "estimated_annual_km": 40000,
            },
            {
                "code": "lcv",
                "display_name": "Light Commercial Vehicle (2-7T)",
                "fuel_efficiency_kmpl": 10.0,
                "toll_rate_per_km": 0.70,
                "capacity_tons": 7.0,
                "capacity_cbm": 24.0,
                "depreciation_annual": 200000,
                "insurance_annual": 35000,
                "driver_salary_annual": 300000,
                "permit_fees_annual": 15000,
                "maintenance_per_km": 2.5,
                "tire_cost_per_km": 1.0,
                "estimated_annual_km": 50000,
            },
            {
                "code": "medium_truck",
                "display_name": "Medium Truck (9-12T)",
                "fuel_efficiency_kmpl": 6.0,
                "toll_rate_per_km": 1.20,
                "capacity_tons": 12.0,
                "capacity_cbm": 40.0,
                "depreciation_annual": 400000,
                "insurance_annual": 60000,
                "driver_salary_annual": 360000,
                "permit_fees_annual": 20000,
                "maintenance_per_km": 3.5,
                "tire_cost_per_km": 1.5,
                "estimated_annual_km": 60000,
            },
            {
                "code": "heavy_truck",
                "display_name": "Heavy / Multi-Axle Truck (20-40T)",
                "fuel_efficiency_kmpl": 4.0,
                "toll_rate_per_km": 2.00,
                "capacity_tons": 40.0,
                "capacity_cbm": 80.0,
                "depreciation_annual": 600000,
                "insurance_annual": 80000,
                "driver_salary_annual": 480000,
                "permit_fees_annual": 30000,
                "maintenance_per_km": 4.0,
                "tire_cost_per_km": 2.0,
                "estimated_annual_km": 80000,
            },
            {
                "code": "trailer",
                "display_name": "Trailer / Container (40T+)",
                "fuel_efficiency_kmpl": 3.5,
                "toll_rate_per_km": 2.50,
                "capacity_tons": 45.0,
                "capacity_cbm": 90.0,
                "depreciation_annual": 900000,
                "insurance_annual": 120000,
                "driver_salary_annual": 480000,
                "permit_fees_annual": 40000,
                "maintenance_per_km": 5.0,
                "tire_cost_per_km": 2.5,
                "estimated_annual_km": 90000,
            },
        ]
        for v in vehicles:
            v_copy = v.copy()
            v_copy.pop('capacity_cbm', None)
            if 'name' not in v_copy:
                v_copy['name'] = v_copy.get('display_name', v_copy['code'])
            VehicleType.objects.get_or_create(code=v_copy['code'], defaults=v_copy)

        # 2. Service Tiers
        tiers = [
            {"code": "standard", "name": "Standard", "multiplier": 1.0},
            {"code": "express", "name": "Express", "multiplier": 1.2},
            {"code": "premium", "name": "Premium", "multiplier": 1.5},
        ]
        for t in tiers:
            ServiceTier.objects.get_or_create(code=t['code'], defaults=t)

        # 3. Customer Segments
        segments = [
            {"code": "individual", "name": "Individual", "discount_percentage": 0.0, "platform_fee_percentage": 5.0},
            {"code": "sme", "name": "SME", "discount_percentage": 5.0, "platform_fee_percentage": 4.0},
            {"code": "enterprise", "name": "Enterprise", "discount_percentage": 10.0, "platform_fee_percentage": 3.0},
            {"code": "contract", "name": "Contract", "discount_percentage": 15.0, "platform_fee_percentage": 2.5},
        ]
        for s in segments:
            CustomerSegment.objects.get_or_create(code=s['code'], defaults=s)

        # 4. VAS
        vas = [
            {"code": "gps_tracking", "name": "Live GPS Tracking", "base_price": 300.0},
            {"code": "multi_stop", "name": "Multi-Stop Delivery", "base_price": 400.0},
            {"code": "helper", "name": "Helper Service", "base_price": 800.0},
        ]
        for v in vas:
            ValueAddedService.objects.get_or_create(code=v['code'], defaults=v)

        # 5. Cities
        cities = [
            {"name": "Chennai", "tier": "metro", "fuel_price": 90.0, "latitude": 13.0827, "longitude": 80.2707},
            {"name": "Hyderabad", "tier": "tier_1", "fuel_price": 92.0, "latitude": 17.3850, "longitude": 78.4867},
            {"name": "Bengaluru", "tier": "metro", "fuel_price": 91.5, "latitude": 12.9716, "longitude": 77.5946},
            {"name": "Kochi", "tier": "tier_1", "fuel_price": 93.0, "latitude": 9.9312, "longitude": 76.2673},
            {"name": "Ooty", "tier": "tier_3", "fuel_price": 95.0, "latitude": 11.4102, "longitude": 76.6950},
        ]
        for c in cities:
            City.objects.get_or_create(name=c['name'], defaults=c)

        # 6. Sample Route
        chennai = City.objects.get(name="Chennai")
        hyderabad = City.objects.get(name="Hyderabad")
        Route.objects.get_or_create(
            origin_city=chennai, 
            dest_city=hyderabad, 
            defaults={
                "slug": "chennai-to-hyderabad",
                "distance_km": 625.0,
                "terrain_grade": 2.0,
                "road_surface_quality": 2.0,
                "traffic_congestion": 4.0,
                "weather_risk": 1.0,
                "toll_gate_density": 3.0,
                "historical_accident_rate": 2.0,
                "border_checkpoint_freq": 2.0,
                "lane_viability": "highly_balanced"
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded pricing data'))
