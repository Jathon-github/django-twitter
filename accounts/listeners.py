def invalidate_user_cache(sender, instance, **kwargs):
    from accounts.services import UserService
    UserService.invalidate_user(instance.id)


def invalidate_profile_cache(sender, instance, **kwargs):
    from accounts.services import UserService
    UserService.invalidate_profile(instance.user_id)
