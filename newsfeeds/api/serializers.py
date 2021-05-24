from rest_framework import serializers
from tweets.api.serializers import TweetSerializer
from newsfeeds.models import NewsFeed


class NewsFeedSerializer(serializers.ModelSerializer):
    tweet = TweetSerializer()

    class Meta:
        model = NewsFeed
        fields = ('id', 'created_at', 'tweet')
