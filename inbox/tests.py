from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification


class NotificationServiceTest(TestCase):
    def setUp(self):
        self.clear_cache()

        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')
        self.tweet = self.create_tweet(self.user1)

    def test_seed_comment_notification(self):
        comment = self.create_comment(self.user1, self.tweet)
        NotificationService.seed_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        comment = self.create_comment(self.user2, self.tweet)
        NotificationService.seed_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_seed_like_notification(self):
        like = self.create_like(self.user1, self.tweet)
        NotificationService.seed_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        like = self.create_like(self.user2, self.tweet)
        NotificationService.seed_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)

        comment = self.create_comment(self.user2, self.tweet)

        like = self.create_like(self.user2, comment)
        NotificationService.seed_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)

        like = self.create_like(self.user1, comment)
        NotificationService.seed_like_notification(like)
        self.assertEqual(Notification.objects.count(), 2)
