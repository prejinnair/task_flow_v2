from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User, UserProfile
from accounts.utils import send_verification_email

@receiver(post_save, sender=User)
def post_save_create_profile_receiver(instance, created, **kwargs):
    if not instance.email:
        return

    if created:
        UserProfile.objects.create(user=instance)
        send_verification_email(instance, action='set_password')
    else:
        try:
            profile = UserProfile.objects.get(user=instance)
            profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)
            send_verification_email(instance, action='set_password')
