from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
)
from comments.api.permissions import IsObjectOwner
from comments.models import Comment
from utils.decorators import required_params


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
    def list(self, request):
        # tweet_id = request.query_params['tweet_id']
        # comments = Comment.objects.filter(tweet_id=tweet_id).order_by('created_at')
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

    def destroy(self, request, pk):
        self.get_object().delete()
        return Response({
            'success': True
        }, status=status.HTTP_200_OK)
