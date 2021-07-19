from django.utils.decorators import method_decorator
from newsfeeds.services import NewsFeedService
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetCreateSerializer,
    TweetSerializer,
    TweetSerializerForDetail,
)
from tweets.models import Tweet
from tweets.services import TweetService
from utils.decorators import required_params
from utils.pagination import EndlessPagination


class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetCreateSerializer
    queryset = Tweet.objects.all()
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(params=['user_id'])
    @method_decorator(ratelimit(key='user_or_ip', rate='5/s', method='GET', block=True))
    def list(self, request):
        user_id = request.query_params['user_id']
        cached_tweets = TweetService.get_cached_tweets(user_id)
        page = self.paginator.paginate_cache_list(cached_tweets, request)
        if page is None:
            query_set = Tweet.objects.filter(user_id=user_id)
            page = self.paginate_queryset(query_set)

        serializer = TweetSerializer(
            page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

    @method_decorator(ratelimit(key='user_or_ip', rate='5/s', method='GET', block=True))
    def retrieve(self, request, pk):
        serializer = TweetSerializerForDetail(
            self.get_object(),
            context={'request': request},
        )
        return Response({'tweet': serializer.data})

    @method_decorator(ratelimit(key='user', rate='1/s', method='POST', block=True))
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))
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
