from accounts.api.serializers import UserSerializerForFriendship
from django.contrib.auth.models import User
from friendships.models import Friendship
from friendships.services import FriendshipService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class FollowingUserIdSetMixin(serializers.ModelSerializer):
    @property
    def following_user_id_set(self):
        user = self.context['request'].user
        if user.is_anonymous:
            return set()
        if hasattr(self, '_following_user_id_set'):
            return self._following_user_id_set

        user_id_set = FriendshipService.get_following_user_id_set(user.id)
        setattr(self, '_following_user_id_set', user_id_set)
        return user_id_set


class FollowerSerializer(FollowingUserIdSetMixin):
    user = UserSerializerForFriendship(source='cache_from_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        return obj.from_user.id in self.following_user_id_set


class FollowingSerializer(FollowingUserIdSetMixin):
    user = UserSerializerForFriendship(source='cache_to_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        return obj.to_user.id in self.following_user_id_set


class FriendshipSerializerForCreate(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('from_user_id', 'to_user_id')

    def validate(self, attrs):
        if attrs['from_user_id'] == attrs['to_user_id']:
            raise ValidationError({
                'message': 'You can not follow yourself.',
            })

        if not User.objects.filter(id=attrs['to_user_id']).exists():
            raise ValidationError({
                'message': 'You can not follow a non-exist user.',
            })

        return attrs

    def create(self, validated_data):
        return Friendship.objects.create(
            from_user_id=validated_data['from_user_id'],
            to_user_id=validated_data['to_user_id']
        )
