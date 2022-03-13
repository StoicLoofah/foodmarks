from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    mostly for preferences
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    copy_tags = models.BooleanField(
        default=True,
        verbose_name="Copy tags when adding someone else's recipe")

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Create a matching profile whenever a user object is created.
    """

    if created:
        profile, new = UserProfile.objects.get_or_create(user=instance)
