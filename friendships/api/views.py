from rest_framework import viewsets, status
from django.contrib.auth.models import User
from friendships.models import Friendship
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from friendships.api.serializers import (
    FollowerSerializer,
    FollowingSerializer,
    FriendshipSerializerForCreate,
)
from rest_framework.response import Response
from utils.paginations import FriendshipPagination


class FriendshipViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = FriendshipSerializerForCreate
    pagination_class = FriendshipPagination

    @action(methods=['GET'], detail=True, permission_classes=(AllowAny,))
    def followers(self, request, pk):
        friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=(AllowAny,))
    def followings(self, request, pk):
        friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=(IsAuthenticated,))
    def follow(self, request, pk):
        if Friendship.objects.filter(from_user=request.user, to_user_id=pk).exists():
            return Response({
                'success': True,
                'duplicate': True,
            }, status=status.HTTP_201_CREATED)

        serializer = FriendshipSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': pk,
        })

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        return Response({
            'user': FollowingSerializer(instance, context={'request': request}).data['user'],
            'success': True,
            'duplicate': False,
        }, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, permission_classes=(IsAuthenticated,))
    def unfollow(self, request, pk):
        deleted, _ = Friendship.objects.filter(
            from_user=request.user,
            to_user_id=pk,
        ).delete()

        return Response({
            'success': True,
            'deleted': deleted,
        })
