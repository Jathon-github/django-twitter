from inbox.api.serializers import (
    NotificationSerializers,
    NotificationSerializersForUpdate,
)
from notifications.models import Notification
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_params


class NotificationViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSerializers
    filterset_fields = ('unread',)

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    def unread_count(self, request):
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        query_set = self.get_queryset().filter(unread=True)
        updated_count = query_set.update(unread=False)
        return Response({
            'marked_count': updated_count,
        }, status=status.HTTP_200_OK)

    @required_params(method='PUT', params=['unread'])
    def update(self, request, pk):
        instance = self.get_object()
        serializer = NotificationSerializersForUpdate(
            instance=instance,
            data=request.data,
        )

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        notification = serializer.save()
        return Response({
            'success': True,
            'notification': NotificationSerializers(notification).data,
        }, status=status.HTTP_200_OK)

