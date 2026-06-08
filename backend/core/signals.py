from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Order
from .tasks import sync_user_to_airtable, sync_order_to_airtable

User = get_user_model()


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """
    Triggers Airtable sync when a User is created or updated.
    """
    transaction.on_commit(lambda: sync_user_to_airtable.delay(instance.id))


@receiver(post_save, sender=Order)
def handle_order_save(sender, instance, created, **kwargs):
    """
    Triggers Airtable sync when an Order is created or updated.
    """
    transaction.on_commit(lambda: sync_order_to_airtable.delay(str(instance.id)))
