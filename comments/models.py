from django.db import models
from django.contrib.auth.models import User
from tweets.models import Tweet


# Create your models here.
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    content = models.CharField(max_length=127)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('tweet', 'created_at'),)

    def __str__(self):
        return f'{self.created_at} - {self.user} says ' \
               f'{self.content} at tweet {self.tweet_id}'
