from utils.listeners import invalidate_object_cache


def incr_likes_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    if not created:
        return

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    Tweet.objects.filter(id=instance.object_id).update(
        likes_count=F('likes_count') + 1,
    )
    invalidate_object_cache(Tweet, instance.content_object)


def decr_likes_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    Tweet.objects.filter(id=instance.object_id).update(
        likes_count=F('likes_count') - 1,
    )
    invalidate_object_cache(Tweet, instance.content_object)
