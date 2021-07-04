from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from tweets.models import Tweet
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient


class NewsFeedServiceTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.user = self.create_user('user')

    def test_get_user_newsfeeds(self):
        newsfeeds = []
        for i in range(3):
            tweet = Tweet.objects.create(user=self.user, content=f'content {i}')
            newsfeed = self.create_newsfeed(self.user, tweet)
            newsfeeds.append(newsfeed)
        newsfeeds.reverse()

        # cache hit
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user.id)
        self.assertEqual(newsfeeds, cached_newsfeeds)

        # cache miss
        RedisClient.clear()
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user.id)
        self.assertEqual(newsfeeds, cached_newsfeeds)

        # cache update
        tweet = Tweet.objects.create(user=self.user, content=f'content {i}')
        newsfeed = self.create_newsfeed(self.user, tweet)
        newsfeeds.insert(0, newsfeed)
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user.id)
        self.assertEqual(newsfeeds, cached_newsfeeds)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        tweet1 = Tweet.objects.create(user=self.user, content=f'content')
        newsfeed1 = self.create_newsfeed(self.user, tweet1)

        RedisClient.clear()
        conn = RedisClient.get_connection()
        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user.id)
        self.assertEqual(conn.exists(key), False)

        tweet2 = Tweet.objects.create(user=self.user, content=f'content')
        newsfeed2 = self.create_newsfeed(self.user, tweet2)
        self.assertEqual(conn.exists(key), True)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user.id)
        self.assertEqual(newsfeeds, [newsfeed2, newsfeed1])
