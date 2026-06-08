from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404

from .models import Item, PricingQuote, Order
from .serializers import (
    ItemSerializer, PricingInputSerializer, PricingQuoteSerializer,
    UserSignupSerializer, OrderSerializer
)
from .tasks import process_item, send_quote_notifications
from .services import PricingEngine, PricingError


class CalculateQuoteView(generics.CreateAPIView):
    """
    API endpoint to calculate a dynamic pricing quote.
    """
    serializer_class = PricingInputSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'quote_calculator'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        notification_contact = data.pop('notification_contact', None)
        notification_type = data.pop('notification_type', 'whatsapp')

        engine = PricingEngine()
        try:
            quote = engine.calculate_quote(
                user=request.user if request.user.is_authenticated else None,
                **data
            )

            # Trigger Background Notification if contact provided
            if notification_contact:
                send_quote_notifications.delay(
                    quote_id=quote.quote_id,
                    recipient_contact=notification_contact,
                    notification_type=notification_type
                )

            return Response(PricingQuoteSerializer(quote).data, status=status.HTTP_201_CREATED)
        except PricingError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_400_BAD_REQUEST)


class ItemListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating Items.

    GET requests return a list of items owned by the current user (or all items
    if the user is a superuser).  POST requests allow the authenticated user
    to create a new item.
    """
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Item.objects.all()
        return Item.objects.filter(owner=user)

    def perform_create(self, serializer: ItemSerializer) -> None:
        serializer.save(owner=self.request.user)


class ItemDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single Item by ID.  Only the owner (or a
    superuser) may access an item.
    """
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Item.objects.all()
        return Item.objects.filter(owner=user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_item_processing(request, pk: int) -> Response:
    """
    API endpoint to start asynchronous processing of an Item.

    When called, this endpoint kicks off a Celery task which will simulate
    heavy work and then update the Item's `processed` flag.  Progress
    notifications will be emitted over a WebSocket at `/ws/items/<pk>/`.
    """
    item = get_object_or_404(Item, pk=pk)
    # Only the owner or superusers can trigger processing
    if item.owner != request.user and not request.user.is_superuser:
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    # Trigger the Celery task
    process_item.delay(item.pk)
    return Response({'status': 'processing started'}, status=status.HTTP_202_ACCEPTED)


class UserSignupView(generics.CreateAPIView):
    """
    API endpoint for Shippers/Transporters registration.
    """
    serializer_class = UserSignupSerializer
    permission_classes = [permissions.AllowAny]


class OrderListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Order.objects.all()
        # If user has a customer profile, return their orders
        if hasattr(user, 'customer_profile'):
            return Order.objects.filter(customer=user.customer_profile)
        return Order.objects.none()


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating an order.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Order.objects.all()
        if hasattr(user, 'customer_profile'):
            return Order.objects.filter(customer=user.customer_profile)
        return Order.objects.none()