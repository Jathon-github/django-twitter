from accounts.listeners import invalidate_profile_cache
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from utils.listeners import invalidate_object_cache


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    avatar = models.FileField(null=True)
    nickname = models.CharField(null=True, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.user, self.nickname)


def get_profile(user):
    from accounts.services import UserService

    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile = UserService.get_profile_through_cache(user.id)
    setattr(user, '_cached_user_profile', profile)
    return profile


User.profile = property(get_profile)

post_save.connect(invalidate_object_cache, sender=User)
pre_delete.connect(invalidate_object_cache, sender=User)

post_save.connect(invalidate_profile_cache, sender=UserProfile)
pre_delete.connect(invalidate_profile_cache, sender=UserProfile)
