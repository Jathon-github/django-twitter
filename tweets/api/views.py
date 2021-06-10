from newsfeeds.services import NewsFeedService
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetCreateSerializer,
    TweetSerializer,
    TweetSerializerForDetail,
)
from tweets.models import Tweet
from utils.decorators import required_params


class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetCreateSerializer
    queryset = Tweet.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(params=['user_id'])
    def list(self, request):
        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(
            tweets,
            context={'request': request},
            many=True,
        )
        return Response({'tweets': serializer.data})

    def retrieve(self, request, pk):
        serializer = TweetSerializerForDetail(
            self.get_object(),
            context={'request': request},
        )
        return Response({'tweet': serializer.data})

    def create(self, request):
        serializer = TweetCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(tweet, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
