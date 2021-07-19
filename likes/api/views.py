from django.utils.decorators import method_decorator
from likes.api.serializers import (
    LikeSerializer,
    LikeSerializerForCancel,
    LikeSerializerForCreate,
)
from likes.models import Like
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_params


class LikeViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Like.objects.all()
    serializer_class = LikeSerializerForCreate

    @required_params(method='POST', params=['content_type', 'object_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='GET', block=True))
    def create(self, request):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request},
        )

        if not serializer.is_valid():
            return Response({
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        return Response({
            'like': LikeSerializer(instance).data,
        }, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False)
    @required_params(method='POST', params=['content_type', 'object_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def cancel(self, request):
        serializer = LikeSerializerForCancel(
            data=request.data,
            context={'request': request},
        )

        if not serializer.is_valid():
            return Response({
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        deleted = serializer.cancel()
        return Response({
            'deleted': deleted,
            'success': True,
        }, status=status.HTTP_200_OK)
