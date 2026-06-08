from __future__ import annotations

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Item, PricingQuote, User, Customer, Consignee, Order, City, VehicleType

User = get_user_model()


class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    gst_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'full_name', 'phone', 'role', 'company_name', 'gst_number')

    def create(self, validated_data):
        company_name = validated_data.pop('company_name', '')
        gst_number = validated_data.pop('gst_number', '')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # If customer role, create customer profile
        if user.role == 'customer':
            Customer.objects.create(
                user=user,
                company_name=company_name,
                gst_number=gst_number
            )
        return user


class ConsigneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consignee
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    consignee = ConsigneeSerializer()
    origin_city_name = serializers.CharField(source='origin_city.name', read_only=True)
    dest_city_name = serializers.CharField(source='dest_city.name', read_only=True)
    vehicle_type_code = serializers.CharField(source='vehicle_type.code', read_only=True)

    # Writable fields using names/codes
    origin_city = serializers.SlugRelatedField(slug_field='name', queryset=City.objects.filter(is_active=True))
    dest_city = serializers.SlugRelatedField(slug_field='name', queryset=City.objects.filter(is_active=True))
    vehicle_type = serializers.SlugRelatedField(slug_field='code', queryset=VehicleType.objects.filter(is_active=True))

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'customer', 'consignee', 'vehicle', 'origin_city', 'dest_city',
            'origin_city_name', 'dest_city_name', 'pickup_address', 'delivery_address',
            'vehicle_type', 'vehicle_type_code', 'tonnage', 'body_dimensions', 'goods_type',
            'pickup_date', 'special_instructions', 'estimated_price', 'status', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'order_number', 'customer', 'vehicle', 'estimated_price', 'status', 'created_at', 'updated_at')

    def create(self, validated_data):
        consignee_data = validated_data.pop('consignee')
        consignee = Consignee.objects.create(**consignee_data)

        # Generate a unique order number (e.g. ORD-YYYYMMDD-XXXX)
        import datetime
        import random
        date_str = datetime.date.today().strftime('%Y%m%d')
        rand_str = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
        order_number = f"ORD-{date_str}-{rand_str}"

        # Fetch customer profile
        request = self.context.get('request')
        user = request.user
        customer, _ = Customer.objects.get_or_create(user=user)

        order = Order.objects.create(
            order_number=order_number,
            customer=customer,
            consignee=consignee,
            **validated_data
        )
        return order


class PricingInputSerializer(serializers.Serializer):
    origin_city = serializers.CharField()
    destination_city = serializers.CharField()
    vehicle_type = serializers.CharField()
    cargo_weight_tons = serializers.FloatField()
    cargo_volume_cbm = serializers.FloatField()
    service_tier = serializers.CharField()
    customer_segment = serializers.CharField()
    value_added_services = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    insurance_tier = serializers.CharField(required=False, default="standard")
    declared_value = serializers.FloatField(required=False, default=0.0)
    loading_unloading_cost = serializers.FloatField(required=False, default=0.0)
    
    # Notification fields
    notification_contact = serializers.CharField(required=False, allow_blank=True)
    notification_type = serializers.ChoiceField(choices=['whatsapp', 'email'], required=False, default='whatsapp')


class PricingQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingQuote
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the Item model.  It includes validation to ensure that
    names are not blank or excessively long.
    """

    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Item
        fields = ('id', 'owner', 'name', 'processed', 'created_at')
        read_only_fields = ('id', 'owner', 'processed', 'created_at')

    def validate_name(self, value: str) -> str:
        """Ensure that the item name is not empty and trim whitespace."""
        if not value or not value.strip():
            raise serializers.ValidationError('Name cannot be blank.')
        value = value.strip()
        if len(value) > 255:
            raise serializers.ValidationError('Name is too long.')
        return value