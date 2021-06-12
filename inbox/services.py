from tweets.models import Tweet
from comments.models import Comment
from notifications.signals import notify


class NotificationService:
    @classmethod
    def seed_like_notification(cls, like):
        target = like.content_object
        if like.user == target.user:
            return

        if target.__class__ == Tweet:
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your tweet',
                target=target,
            )

        if target.__class__ == Comment:
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your comment',
                target=target,
            )

    @classmethod
    def seed_comment_notification(cls, comment):
        tweet = comment.tweet
        if tweet.user == comment.user:
            return

        notify.send(
            sender=comment.user,
            recipient=tweet.user,
            verb='commented on your tweet',
            target=comment.tweet,
        )
