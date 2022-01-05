from django.db.models.signals import post_save
from .models import Order
from django.dispatch import receiver

@receiver(post_save, sender=Order)

def start_order_processing(sender, instance, created, **kwargs):
    # Run only if it is a new order
    if created:
        print('Hit start_order_processing')
        # Profile.objects.create(user=instance)

# @receiver(post_save, sender=Order)
# def save_user_profile(sender, instance, **kwargs):
#     instance.save()
