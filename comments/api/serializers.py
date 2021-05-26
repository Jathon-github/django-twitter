from rest_framework import serializers
from comments.models import Comment
from accounts.api.serializers import UserSerializerForComment
from tweets.models import Tweet
from rest_framework.exceptions import ValidationError


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment()

    class Meta:
        model = Comment
        fields = ('id', 'tweet_id', 'user', 'content', 'created_at')


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
        return Comment.objects.create(
            tweet_id=validated_data['tweet_id'],
            user_id=validated_data['user_id'],
            content=validated_data['content'],
        )
