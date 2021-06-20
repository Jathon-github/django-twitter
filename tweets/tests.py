from datetime import timedelta
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import TweetPhoto
from utils.time_helpers import utc_now


class TweetTests(TestCase):
    def setUp(self):
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


class TweetPhotoTests(TestCase):
    def setUp(self):
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
