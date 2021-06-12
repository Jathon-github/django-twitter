from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'


class NotificationServiceApiTest(TestCase):
    def setUp(self):
        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')
        self.tweet = self.create_tweet(self.user1)

    def test_seed_comment_notification(self):
        self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'first comment',
        })
        self.assertEqual(Notification.objects.count(), 0)

        self.user2_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'first comment',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_seed_like_notification(self):
        self.user1_client.post(LIKE_URL, {'content_type': 'tweet', 'object_id': self.tweet.id})
        self.assertEqual(Notification.objects.count(), 0)

        self.user2_client.post(LIKE_URL, {'content_type': 'tweet', 'object_id': self.tweet.id})
        self.assertEqual(Notification.objects.count(), 1)

        comment = self.create_comment(self.user2, self.tweet)

        self.user2_client.post(LIKE_URL, {'content_type': 'comment', 'object_id': comment.id})
        self.assertEqual(Notification.objects.count(), 1)

        self.user1_client.post(LIKE_URL, {'content_type': 'comment', 'object_id': comment.id})
        self.assertEqual(Notification.objects.count(), 2)
