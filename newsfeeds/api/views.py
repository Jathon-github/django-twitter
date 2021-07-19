from django.utils.decorators import method_decorator
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from ratelimit.decorators import ratelimit
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.pagination import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    @method_decorator(ratelimit(key='user', rate='5/s', method='GET', block=True))
    def list(self, request):
        user_id = request.user.id
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(user_id)
        page = self.paginator.paginate_cache_list(cached_newsfeeds, request)
        if page is None:
            query_set = NewsFeed.objects.filter(user_id=request.user.id)
            page = self.paginate_queryset(query_set)

        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True,
        )

        return self.get_paginated_response(serializer.data)
