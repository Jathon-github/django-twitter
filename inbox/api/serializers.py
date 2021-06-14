from notifications.models import Notification
from rest_framework import serializers


class NotificationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Notification

        fields = (
            'id',
            'actor_content_type',
            'actor_object_id',
            'verb',
            'action_object_content_type',
            'action_object_object_id',
            'target_content_type',
            'target_object_id',
            'timestamp',
            'unread',
        )


class NotificationSerializersForUpdate(serializers.ModelSerializer):
    unread = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = (
            'unread',
        )

    def update(self, instance, validated_data):
        unread = validated_data['unread']
        instance.unread = unread
        instance.save()
        return instance
