from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.tasks import fanout_newsfeeds_main_task
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


class NewsFeedTaskTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.user = self.create_user('user')

    def test_fanout_main_task(self):
        MASSAGE = '{} newsfeeds going to fanout, {} batches created.'

        tweet = self.create_tweet(self.user)
        user1 = self.create_user('follower 1')
        self.create_friendship(user1, self.user)
        massage = fanout_newsfeeds_main_task(tweet.id, tweet.user_id)
        self.assertEqual(massage, MASSAGE.format(1, 1))
        self.assertEqual(1 + 1, NewsFeed.objects.count())

        tweet = self.create_tweet(self.user)
        user2 = self.create_user('follower 2')
        self.create_friendship(user2, self.user)
        massage = fanout_newsfeeds_main_task(tweet.id, tweet.user_id)
        self.assertEqual(massage, MASSAGE.format(2, 1))
        self.assertEqual(3 + 2, NewsFeed.objects.count())

        tweet = self.create_tweet(self.user)
        user3 = self.create_user('follower 3')
        self.create_friendship(user3, self.user)
        massage = fanout_newsfeeds_main_task(tweet.id, tweet.user_id)
        self.assertEqual(massage, MASSAGE.format(3, 1))
        self.assertEqual(6 + 3, NewsFeed.objects.count())

        tweet = self.create_tweet(self.user)
        user4 = self.create_user('follower 4')
        self.create_friendship(user4, self.user)
        massage = fanout_newsfeeds_main_task(tweet.id, tweet.user_id)
        self.assertEqual(massage, MASSAGE.format(4, 2))
        self.assertEqual(10 + 4, NewsFeed.objects.count())
