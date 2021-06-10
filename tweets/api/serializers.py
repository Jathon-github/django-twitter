from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from likes.services import LikeServices
from rest_framework import serializers
from rest_framework.serializers import CharField
from tweets.models import Tweet


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()
    has_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'created_at',
            'content',
            'user',
            'has_liked',
            'comments_count',
            'likes_count',
        )

    def get_has_liked(self, obj):
        return LikeServices.has_liked(self.context['request'].user, obj)

    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_likes_count(self, obj):
        return obj.like_set.count()


class TweetSerializerForDetail(TweetSerializer):
    comments = CommentSerializer(source='comment_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments',
            'has_liked',
            'comments_count',
            'likes_count',
        )


class TweetCreateSerializer(serializers.ModelSerializer):
    content = CharField(min_length=6, max_length=255)

    class Meta:
        model = Tweet
        fields = ('content',)

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet
