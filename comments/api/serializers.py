from accounts.api.serializers import UserSerializerForComment
from comments.models import Comment
from inbox.services import NotificationService
from likes.services import LikeServices
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.models import Tweet


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment(source='cached_user')
    has_liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'tweet_id',
            'user',
            'content',
            'created_at',
            'has_liked',
            'likes_count',
        )

    def get_has_liked(self, obj):
        return LikeServices.has_liked(self.context['request'].user, obj)

    def get_likes_count(self, obj):
        return obj.like_set.count()


class CommentSerializerForCreate(serializers.ModelSerializer):
    tweet_id = serializers.IntegerField()
    user_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ('content', 'tweet_id', 'user_id')

    def validate(self, attrs):
        tweet_id = attrs['tweet_id']
        if not Tweet.objects.filter(id=tweet_id).exists():
            raise ValidationError({'message': 'tweet does not exist'})
        return attrs

    def create(self, validated_data):
        instance = Comment.objects.create(
            tweet_id=validated_data['tweet_id'],
            user_id=validated_data['user_id'],
            content=validated_data['content'],
        )
        NotificationService.seed_comment_notification(instance)
        return instance
