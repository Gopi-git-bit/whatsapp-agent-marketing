import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# ==============================================================================
# 1. CORE DOMAIN (Users, Customers, Consignees)
# ==============================================================================

class User(AbstractUser):
    """
    Custom User model extending Django's default AbstractUser.
    Maps to the `users` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)  # WhatsApp number
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=[
            ('customer', 'Customer'),
            ('vehicle_owner', 'Vehicle Owner'),
            ('admin', 'Admin')
        ],
        default='customer'
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Customer(models.Model):
    """
    Maps to the `customers` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    company_name = models.CharField(max_length=255, null=True, blank=True)
    gst_number = models.CharField(max_length=20, null=True, blank=True)
    default_origin = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name or self.user.full_name


class Consignee(models.Model):
    """
    Maps to the `consignees` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ==============================================================================
# 2. PRICING & FLEET DOMAIN (Vehicle Types, Vehicles, Cities, Routes)
# ==============================================================================

class VehicleType(models.Model):
    """
    Maps to the `vehicle_types` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # Truck, Trailer, Container, Mini Truck
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    capacity_tons = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    body_type = models.CharField(max_length=50, null=True, blank=True)  # Open, Closed, Flatbed, Tanker
    length_ft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width_ft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height_ft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Financial/Cost Amortization fields for DPYMA
    fuel_efficiency_kmpl = models.DecimalField(max_digits=5, decimal_places=2, default=4.00)
    toll_rate_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    estimated_annual_km = models.DecimalField(max_digits=12, decimal_places=2, default=60000.00)
    driver_salary_annual = models.DecimalField(max_digits=12, decimal_places=2, default=300000.00)
    depreciation_annual = models.DecimalField(max_digits=12, decimal_places=2, default=150000.00)
    insurance_annual = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    permit_fees_annual = models.DecimalField(max_digits=12, decimal_places=2, default=20000.00)
    maintenance_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=2.00)
    tire_cost_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=1.50)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.body_type})"


class Vehicle(models.Model):
    """
    Maps to the `vehicles` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE, related_name='vehicles')
    registration_no = models.CharField(max_length=50, unique=True, null=True, blank=True)
    current_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    current_city = models.CharField(max_length=100, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.registration_no or f"Vehicle-{self.id.hex[:6]}"


class City(models.Model):
    """
    Maps to the `cities` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    cluster = models.CharField(max_length=100, null=True, blank=True)  # Chennai, Bangalore, Western TN
    tier = models.CharField(max_length=20, default='tier_2')  # metro, tier_1, tier_2, tier_3, semi_urban, rural
    fuel_price = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Route(models.Model):
    """
    Maps to the `routes` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origin_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='routes_origin')
    dest_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='routes_destination')
    slug = models.SlugField(max_length=255, unique=True)  # "chennai-to-coimbatore"
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    avg_duration_hrs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lane_viability = models.CharField(max_length=50, default='highly_balanced')  # highly_balanced, etc.
    
    # RDS fields for DPYMA
    terrain_grade = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    road_surface_quality = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    traffic_congestion = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    weather_risk = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    toll_gate_density = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    historical_accident_rate = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    border_checkpoint_freq = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)

    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    negative_keywords = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    image_url = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.origin_city.name} -> {self.dest_city.name}"


class ServiceTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)

    def __str__(self):
        return self.name


class CustomerSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    platform_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name


class ValueAddedService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PricingQuote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote_id = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='quotes')
    origin_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE, related_name='quotes')
    cargo_weight_tons = models.DecimalField(max_digits=10, decimal_places=2)
    cargo_volume_cbm = models.DecimalField(max_digits=10, decimal_places=2)
    service_tier = models.ForeignKey(ServiceTier, on_delete=models.CASCADE, related_name='quotes')
    customer_segment = models.ForeignKey(CustomerSegment, on_delete=models.CASCADE, related_name='quotes')
    final_total = models.DecimalField(max_digits=12, decimal_places=2)
    breakdown = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quote_id} ({self.origin_city} -> {self.destination_city})"


# ==============================================================================
# 3. BOOKING & TRANSACTION DOMAIN (Orders, Payments, Waiting List)
# ==============================================================================

class Order(models.Model):
    """
    Maps to the `orders` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True)  # ORD-20260607-001
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    consignee = models.ForeignKey(Consignee, on_delete=models.CASCADE, related_name='orders')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    origin_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='orders_origin')
    dest_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='orders_destination')
    pickup_address = models.TextField()
    delivery_address = models.TextField()
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE, related_name='orders')
    tonnage = models.DecimalField(max_digits=10, decimal_places=2)
    body_dimensions = models.JSONField(null=True, blank=True)  # {"length":20,"width":7,"height":7}
    goods_type = models.CharField(max_length=255, null=True, blank=True)
    pickup_date = models.DateField()
    special_instructions = models.TextField(null=True, blank=True)
    estimated_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('confirmed', 'Confirmed'),
            ('waiting', 'Waiting'),
            ('suspended', 'Suspended'),
            ('failed', 'Failed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='waiting'
    )
    whatsapp_message_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number


class PaymentTransaction(models.Model):
    """
    Maps to the `payment_transactions` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    transaction = models.CharField(max_length=100, unique=True, null=True, blank=True)  # Payment gateway reference
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    payment_method = models.CharField(max_length=50, null=True, blank=True)  # UPI, Bank Transfer, etc.
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded')
        ],
        default='pending'
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment-{self.id.hex[:6]}"


class WaitingList(models.Model):
    """
    Maps to the `waiting_list` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='waiting_list_entries')
    origin_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='waiting_list_origins')
    dest_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='waiting_list_destinations')
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE, related_name='waiting_list_entries')
    tonnage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    required_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('waiting', 'Waiting'),
            ('matched', 'Matched'),
            ('expired', 'Expired')
        ],
        default='waiting'
    )
    notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Waiting-{self.id.hex[:6]}"


# ==============================================================================
# 4. CONTENT & OTHER DOMAINS (Blog Posts, FAQs)
# ==============================================================================

class BlogPost(models.Model):
    """
    Maps to the `blog_posts` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    featured_image = models.CharField(max_length=500, null=True, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    author = models.CharField(max_length=100, default='AI Writer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """
    Maps to the `faqs` table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100, null=True, blank=True)  # general, pricing, booking, tracking
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


# Keep the Item model for backward compatibility with existing tasks
class Item(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} (processed={self.processed})"
