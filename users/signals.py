from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from .models import User

@receiver(post_save, sender=SocialAccount)
def save_telegram_id(sender, instance, created, **kwargs):
    if instance.provider == 'telegram':
        user = instance.user
        telegram_id = instance.uid
        if user.telegram_id != telegram_id:
            user.telegram_id = telegram_id
            user.save()