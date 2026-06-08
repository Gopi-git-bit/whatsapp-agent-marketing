from __future__ import annotations

import time
import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Item, PricingQuote

logger = get_task_logger(__name__)


@shared_task(
    bind=True, 
    max_retries=3, 
    default_retry_delay=60, 
    autoretry_for=(Exception,),
    retry_backoff=True
)
def send_quote_notifications(self, quote_id: str, recipient_contact: str, notification_type: str = 'whatsapp') -> None:
    """
    Task to send pricing quote notifications via WhatsApp or Email.
    """
    import os
    if self.request.retries > 0:
        logger.warning(f"Retry {self.request.retries}/3 for notification {quote_id} to {recipient_contact}")

    try:
        quote = PricingQuote.objects.get(quote_id=quote_id)

        if notification_type == 'whatsapp':
            provider = os.getenv('WHATSAPP_PROVIDER', 'generic').lower()
            api_url = os.getenv('WHATSAPP_API_URL')
            api_key = os.getenv('WHATSAPP_API_KEY')
            sender = os.getenv('WHATSAPP_SENDER_NUMBER', '')
            
            message_text = f"Quote {quote_id} generated successfully! Final total: {quote.final_total} INR. View details on your dashboard."
            
            if provider == 'twilio' and api_url and api_key:
                import requests
                auth = (os.getenv('TWILIO_ACCOUNT_SID', ''), api_key)
                payload = {
                    'From': sender if sender.startswith('whatsapp:') else f'whatsapp:{sender}',
                    'To': recipient_contact if recipient_contact.startswith('whatsapp:') else f'whatsapp:{recipient_contact}',
                    'Body': message_text
                }
                response = requests.post(api_url, data=payload, auth=auth, timeout=10)
                response.raise_for_status()
                logger.info(f"Twilio WhatsApp sent successfully: {response.json().get('sid')}")
                
            elif provider == 'whapi' and api_url and api_key:
                import requests
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'to': recipient_contact,
                    'body': message_text
                }
                response = requests.post(f"{api_url.rstrip('/')}/messages/text", json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                logger.info("Whapi WhatsApp sent successfully.")
                
            elif api_url:
                import requests
                headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
                payload = {
                    'to': recipient_contact,
                    'message': message_text,
                    'quote_id': quote_id,
                    'total': float(quote.final_total)
                }
                response = requests.post(api_url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                logger.info("Generic WhatsApp sent successfully.")
            else:
                logger.warning("WhatsApp credentials or API URL not set in environment. Simulating dispatch.")
                print(f"SENDING WHATSAPP to {recipient_contact}: Quote {quote_id} for {quote.final_total} INR")

        elif notification_type == 'email':
            # Logic for Email API (e.g., SendGrid, Mailgun)
            print(f"SENDING EMAIL to {recipient_contact}: Quote {quote_id}")

        # Update WebSockets if a channel exists for this user/quote
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'notifications_{quote.owner.id if quote.owner else "public"}',
                {
                    'type': 'notification.sent',
                    'message': {
                        'status': 'sent',
                        'quote_id': quote_id,
                        'type': notification_type
                    },
                },
            )
    except PricingQuote.DoesNotExist:
        logger.error(f"Quote {quote_id} not found for notification.")
    except Exception as exc:
        logger.error(f"Error sending notification {quote_id}: {str(exc)}")
        raise exc


@shared_task(bind=True)
def process_item(self, item_id: int) -> None:
    """
    A Celery task that simulates a long‑running job for an Item.  It sends
    progress updates over a WebSocket channel group named `item_{id}`.  When
    finished, it marks the item as processed.

    Args:
        item_id: Primary key of the Item to process.
    """
    channel_layer = get_channel_layer()
    group_name = f'item_{item_id}'

    # Send an initial message
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'progress.update',
            'message': {'status': 'started', 'progress': 0},
        },
    )
    # Simulate work in increments
    total_steps = 5
    for step in range(1, total_steps + 1):
        time.sleep(1)  # Simulated computation
        progress = int(step / total_steps * 100)
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'progress.update',
                'message': {'status': 'processing', 'progress': progress},
            },
        )

    # Mark the item as processed
    try:
        with transaction.atomic():
            item = Item.objects.select_for_update().get(pk=item_id)
            item.processed = True
            item.save(update_fields=['processed'])
    except Item.DoesNotExist:
        # If the item was deleted mid-process, send an error
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'progress.update',
                'message': {'status': 'error', 'detail': 'Item not found'},
            },
        )
        return
    # Send final completion message
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'progress.update',
            'message': {'status': 'completed', 'progress': 100},
        },
    )


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def sync_user_to_airtable(self, user_id: int) -> None:
    """
    Task to sync a newly created or updated User to Airtable as a read-only mirror.
    """
    import os
    import requests
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    airtable_token = os.getenv('AIRTABLE_ACCESS_TOKEN')
    airtable_base = os.getenv('AIRTABLE_BASE_ID')
    airtable_table = os.getenv('AIRTABLE_USERS_TABLE', 'Users')
    
    if not (airtable_token and airtable_base):
        logger.warning("Airtable credentials (token or base ID) are not configured. Skipping sync.")
        return

    try:
        user = User.objects.get(pk=user_id)
        role = user.role
        email = user.email
        phone = user.phone_number or ""
        company = ""
        is_active = user.is_active
        
        if role == 'customer' and hasattr(user, 'customer_profile'):
            profile = user.customer_profile
            company = profile.company_name or ""
        elif role == 'vehicle_owner' and hasattr(user, 'transporter_profile'):
            profile = user.transporter_profile
            company = profile.company_name or ""
            
        fields = {
            "User ID": str(user.id),
            "Username": user.username,
            "Email": email,
            "Phone Number": phone,
            "Role": role,
            "Company Name": company,
            "Is Active": is_active,
            "Date Joined": user.date_joined.isoformat() if user.date_joined else ""
        }
        
        url = f"https://api.airtable.com/v0/{airtable_base}/{airtable_table}"
        headers = {
            "Authorization": f"Bearer {airtable_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "performUpsert": {
                "fieldsToMergeOn": ["User ID"]
            },
            "records": [
                {
                    "fields": fields
                }
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"User {user_id} successfully synced to Airtable.")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for Airtable sync.")
    except Exception as exc:
        logger.error(f"Error syncing user {user_id} to Airtable: {str(exc)}")
        raise exc


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def sync_order_to_airtable(self, order_id: str) -> None:
    """
    Task to sync a newly created or updated Order to Airtable as a read-only mirror.
    """
    import os
    import requests
    from .models import Order
    
    airtable_token = os.getenv('AIRTABLE_ACCESS_TOKEN')
    airtable_base = os.getenv('AIRTABLE_BASE_ID')
    airtable_table = os.getenv('AIRTABLE_ORDERS_TABLE', 'Orders')
    
    if not (airtable_token and airtable_base):
        logger.warning("Airtable credentials (token or base ID) are not configured. Skipping sync.")
        return

    try:
        order = Order.objects.get(pk=order_id)
        
        fields = {
            "Order ID": str(order.id),
            "Tracking Number": order.tracking_number,
            "Shipper Username": order.customer.user.username if order.customer else "",
            "Service Tier": order.service_tier.name if order.service_tier else "",
            "Pickup Address": order.pickup_address,
            "Delivery Address": order.delivery_address,
            "Status": order.status,
            "Total Freight Cost": float(order.total_freight_cost),
            "Created At": order.created_at.isoformat() if order.created_at else ""
        }
        
        url = f"https://api.airtable.com/v0/{airtable_base}/{airtable_table}"
        headers = {
            "Authorization": f"Bearer {airtable_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "performUpsert": {
                "fieldsToMergeOn": ["Order ID"]
            },
            "records": [
                {
                    "fields": fields
                }
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Order {order_id} successfully synced to Airtable.")
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for Airtable sync.")
    except Exception as exc:
        logger.error(f"Error syncing order {order_id} to Airtable: {str(exc)}")
        raise exc