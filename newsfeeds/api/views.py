from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.services import NewsFeedService
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.pagination import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def list(self, request):
        query_set = NewsFeedService.get_cached_newsfeeds(request.user.id)
        newsfeeds = self.paginate_queryset(query_set)

        serializer = NewsFeedSerializer(
            newsfeeds,
            context={'request': request},
            many=True,
        )

        return self.get_paginated_response(serializer.data)
