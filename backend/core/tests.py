from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core.models import (
    City, Route, VehicleType, ServiceTier, 
    CustomerSegment, ValueAddedService, PricingQuote
)
from core.services import PricingEngine, PricingError


class PricingEngineTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='shipper_test',
            email='test@example.com',
            password='password123',
            full_name='Test Shipper'
        )

        # Create Cities
        self.chennai = City.objects.create(
            name='Chennai',
            state='Tamil Nadu',
            latitude=Decimal('13.0827'),
            longitude=Decimal('80.2707'),
            cluster='Chennai Metro',
            tier='metro',
            fuel_price=Decimal('102.63')
        )
        self.bangalore = City.objects.create(
            name='Bangalore',
            state='Karnataka',
            latitude=Decimal('12.9716'),
            longitude=Decimal('77.5946'),
            cluster='Bangalore',
            tier='metro',
            fuel_price=Decimal('101.94')
        )

        # Create Route
        self.route = Route.objects.create(
            origin_city=self.chennai,
            dest_city=self.bangalore,
            slug='chennai-to-bangalore',
            distance_km=Decimal('350.00'),
            avg_duration_hrs=Decimal('6.50'),
            lane_viability='highly_balanced',
            terrain_grade=Decimal('1.0'),
            road_surface_quality=Decimal('1.0'),
            traffic_congestion=Decimal('1.2'),
            weather_risk=Decimal('1.0'),
            toll_gate_density=Decimal('1.5'),
            historical_accident_rate=Decimal('1.0'),
            border_checkpoint_freq=Decimal('1.0')
        )

        # Create Vehicle Type
        self.truck = VehicleType.objects.create(
            name='Open Truck (3.5T)',
            code='open_3.5t',
            display_name='3.5 Ton Open Truck',
            capacity_tons=Decimal('3.50'),
            body_type='Open',
            length_ft=Decimal('14.00'),
            width_ft=Decimal('6.00'),
            height_ft=Decimal('6.00'),
            fuel_efficiency_kmpl=Decimal('6.00'),
            toll_rate_per_km=Decimal('3.50'),
            estimated_annual_km=Decimal('50000.00'),
            driver_salary_annual=Decimal('240000.00'),
            depreciation_annual=Decimal('120000.00'),
            insurance_annual=Decimal('30000.00'),
            permit_fees_annual=Decimal('15000.00'),
            maintenance_per_km=Decimal('1.80'),
            tire_cost_per_km=Decimal('1.20')
        )

        # Create Service Tier
        self.standard_tier = ServiceTier.objects.create(
            code='standard',
            name='Standard Delivery',
            multiplier=Decimal('1.00')
        )

        # Create Customer Segment
        self.retail_segment = CustomerSegment.objects.create(
            code='retail',
            name='Retail Customer',
            discount_percentage=Decimal('0.00'),
            platform_fee_percentage=Decimal('5.00')
        )

        # Create VAS
        self.helper = ValueAddedService.objects.create(
            code='helper',
            name='Cargo Helper',
            base_price=Decimal('1200.00'),
            is_active=True
        )

    def test_calculate_quote_success(self):
        engine = PricingEngine()
        quote = engine.calculate_quote(
            user=self.user,
            origin_name='Chennai',
            destination_name='Bangalore',
            vehicle_code='open_3.5t',
            cargo_weight=2.5,
            cargo_volume=10.0,
            service_tier_code='standard',
            customer_segment_code='retail',
            vas_codes=['helper'],
            insurance_tier='standard',
            declared_value=50000.0,
            loading_unloading_cost=500.00,
            demand_multiplier=1.0
        )

        # Assertions
        self.assertIsNotNone(quote)
        self.assertEqual(quote.origin_city, 'Chennai')
        self.assertEqual(quote.destination_city, 'Bangalore')
        self.assertEqual(quote.vehicle_type, self.truck)
        self.assertEqual(quote.service_tier, self.standard_tier)
        self.assertEqual(quote.customer_segment, self.retail_segment)
        self.assertGreater(quote.final_total, Decimal('0.00'))
        
        # Verify database record was created
        self.assertTrue(PricingQuote.objects.filter(quote_id=quote.quote_id).exists())


from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from core.models import Customer, Order


class UserSignupAPITestCase(APITestCase):
    def test_customer_signup_success(self):
        url = reverse('user-signup')
        data = {
            'username': 'new_customer',
            'email': 'customer@example.com',
            'password': 'securepassword123',
            'role': 'customer',
            'full_name': 'New Customer User',
            'phone': '+919876543210',
            'company_name': 'Acme Corp'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'new_customer')
        self.assertTrue(Customer.objects.filter(company_name='Acme Corp').exists())

    def test_transporter_signup_success(self):
        url = reverse('user-signup')
        data = {
            'username': 'new_transporter',
            'email': 'transporter@example.com',
            'password': 'securepassword123',
            'role': 'vehicle_owner',
            'full_name': 'New Transporter User',
            'phone': '+919876543211',
            'company_name': 'Transports Ltd'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'new_transporter')
        User = get_user_model()
        self.assertTrue(User.objects.filter(username='new_transporter', role='vehicle_owner').exists())


class OrderAPITestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='shipper_api_test',
            email='shipper_api@example.com',
            password='password123',
            role='customer'
        )
        self.customer = Customer.objects.create(
            user=self.user,
            company_name='Shipper Inc'
        )
        
        # Create Cities and VehicleType which are active
        self.chennai = City.objects.create(
            name='Chennai',
            state='Tamil Nadu',
            latitude=Decimal('13.0827'),
            longitude=Decimal('80.2707'),
            cluster='Chennai Metro',
            tier='metro',
            fuel_price=Decimal('102.63'),
            is_active=True
        )
        self.bangalore = City.objects.create(
            name='Bangalore',
            state='Karnataka',
            latitude=Decimal('12.9716'),
            longitude=Decimal('77.5946'),
            cluster='Bangalore',
            tier='metro',
            fuel_price=Decimal('101.94'),
            is_active=True
        )
        self.truck = VehicleType.objects.create(
            name='Open Truck (3.5T)',
            code='open_3.5t',
            display_name='3.5 Ton Open Truck',
            capacity_tons=Decimal('3.50'),
            body_type='Open',
            length_ft=Decimal('14.00'),
            width_ft=Decimal('6.00'),
            height_ft=Decimal('6.00'),
            fuel_efficiency_kmpl=Decimal('6.00'),
            toll_rate_per_km=Decimal('3.50'),
            estimated_annual_km=Decimal('50000.00'),
            driver_salary_annual=Decimal('240000.00'),
            depreciation_annual=Decimal('120000.00'),
            insurance_annual=Decimal('30000.00'),
            permit_fees_annual=Decimal('15000.00'),
            maintenance_per_km=Decimal('1.80'),
            tire_cost_per_km=Decimal('1.20'),
            is_active=True
        )

        # Create Service Tier
        self.premium_tier = ServiceTier.objects.create(
            code='premium',
            name='Premium Delivery',
            multiplier=Decimal('1.50')
        )

    def test_order_creation_requires_auth(self):
        url = reverse('order-list-create')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_creation_success(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list-create')
        data = {
            'origin_city': 'Chennai',
            'dest_city': 'Bangalore',
            'pickup_address': '123, Anna Salai, Chennai',
            'delivery_address': '456, MG Road, Bangalore',
            'vehicle_type': 'open_3.5t',
            'tonnage': '2.5',
            'pickup_date': '2026-06-15',
            'consignee': {
                'name': 'Consignee Name',
                'phone': '+919999988888'
            },
            'goods_type': 'Heavy equipment'
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("ORDER CREATION FAILED WITH DATA:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Order.objects.filter(goods_type='Heavy equipment').exists())
        
        # Verify listing orders
        list_response = self.client.get(url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)


