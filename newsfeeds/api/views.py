from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.pagination import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        newsfeeds = self.paginate_queryset(self.get_queryset())

        serializer = NewsFeedSerializer(
            newsfeeds,
            context={'request': request},
            many=True,
        )

        return self.get_paginated_response(serializer.data)
