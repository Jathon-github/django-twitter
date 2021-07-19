from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
)
from comments.models import Comment
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
from utils.decorators import required_params
from utils.permissions import IsObjectOwner


class CommentViewSet(viewsets.GenericViewSet):
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    filterset_fields = ('tweet_id',)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action == 'destroy':
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    @required_params(params=['tweet_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='GET', block=True))
    def list(self, request):
        comments = self.filter_queryset(
            self.get_queryset(),
        ).order_by('created_at')
        serializer = CommentSerializer(
            comments,
            context={'request': request},
            many=True,
        )
        return Response({
            'comments': serializer.data,
            'success': True,
        }, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def create(self, request):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }

        serializer = CommentSerializerForCreate(data=data)
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()
        return Response({
            'comment':
                CommentSerializer(comment, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)

    @method_decorator(ratelimit(key='user', rate='5/s', method='DELETE', block=True))
    def destroy(self, request, pk):
        self.get_object().delete()
        return Response({
            'success': True
        }, status=status.HTTP_200_OK)
