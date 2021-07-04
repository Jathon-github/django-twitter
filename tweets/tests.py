from datetime import timedelta
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import TweetPhoto
from tweets.services import TweetService
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from utils.time_helpers import utc_now


class TweetTests(TestCase):
    def setUp(self):
        self.clear_cache()

        self.user = self.create_user('user')
        self.tweet = self.create_tweet(self.user)

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.user, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.user, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.create_user('other_user'), self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_cache_tweet_in_redis(self):
        conn = RedisClient.get_connection()
        serialized_tweet = DjangoModelSerializer.serializer(self.tweet)
        conn.set(f'tweet:{self.tweet.id}', serialized_tweet)

        serialized_tweet = conn.get(f'tweet: not_exists_tweet')
        self.assertEqual(serialized_tweet, None)

        serialized_tweet = conn.get(f'tweet:{self.tweet.id}')
        cache_tweet = DjangoModelSerializer.deserializer(serialized_tweet)
        self.assertEqual(self.tweet, cache_tweet)


class TweetPhotoTests(TestCase):
    def setUp(self):
        self.clear_cache()

        self.user = self.create_user('user')
        self.tweet = self.create_tweet(self.user)

    def test_created_photo(self):
        photo = TweetPhoto.objects.create(
            user=self.user,
            tweet=self.tweet,
        )
        self.assertEqual(photo.user, self.user)
        self.assertEqual(photo.tweet, self.tweet)
        self.assertEqual(self.tweet.tweetphoto_set.count(), 1)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)


class TweetServiceTests(TestCase):
    def setUp(self):
        self.clear_cache()

    def test_get_user_tweets(self):
        user = self.create_user('user')
        tweets = []
        for i in range(3):
            tweet = self.create_tweet(user)
            tweets.append(tweet)
        tweets.reverse()

        # cache hit
        cached_tweets = TweetService.get_cached_tweets(user_id=user.id)
        self.assertEqual(tweets, cached_tweets)

        # cache miss
        RedisClient.clear()
        cached_tweets = TweetService.get_cached_tweets(user_id=user.id)
        self.assertEqual(tweets, cached_tweets)

        # cache update
        new_tweet = self.create_tweet(user)
        tweets.insert(0, new_tweet)
        cached_tweets = TweetService.get_cached_tweets(user_id=user.id)
        self.assertEqual(tweets, cached_tweets)
