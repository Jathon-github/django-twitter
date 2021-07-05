from notifications.models import Notification
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_LIST_URL = '/api/notifications/'
NOTIFICATION_UPDATE_URL = '/api/notifications/{}/'
NOTIFICATION_UNREAD_COUNT_URL = '/api/notifications/unread-count/'
NOTIFICATION_MARK_ALL_AS_READ_URL = '/api/notifications/mark-all-as-read/'


class NotificationTests(TestCase):
    def setUp(self):
        self.clear_cache()

        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')
        self.tweet = self.create_tweet_with_newsfeed(self.user1)

    def test_seed_comment_notification(self):
        self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'comment',
        })
        self.assertEqual(Notification.objects.count(), 0)

        self.user2_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'comment',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_seed_like_notification(self):
        self.user1_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 0)

        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)

        comment = self.create_comment(self.user2, self.tweet)

        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        self.assertEqual(Notification.objects.count(), 1)

        self.user1_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        self.assertEqual(Notification.objects.count(), 2)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.clear_cache()

        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')
        self.user1_tweet = self.create_tweet_with_newsfeed(self.user1)

    def test_unread_count(self):
        response = self.anonymous_client.get(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.post(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, 405)

        response = self.user1_client.get(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 0)

        self.user2_client.post(COMMENT_URL, {
            'tweet_id': self.user1_tweet.id,
            'content': 'comment',
        })

        response = self.user1_client.get(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 1)
        response = self.user2_client.get(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_all_as_read(self):
        # test anonymous_client
        response = self.anonymous_client.get(NOTIFICATION_MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 403)

        # test get
        response = self.user1_client.get(NOTIFICATION_MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 405)

        # created 3 notifications
        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.user1_tweet.id,
        })
        comment = self.create_comment(self.user1, self.user1_tweet)
        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': self.user1_tweet.id,
            'content': comment,
        })
        response = self.user1_client.get(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 3)

        # test user2 mark all as read
        response = self.user2_client.post(NOTIFICATION_MARK_ALL_AS_READ_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 0)
        response = self.user1_client.get(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 3)

        # test user1 mark all as read
        response = self.user1_client.post(NOTIFICATION_MARK_ALL_AS_READ_URL)
        self.assertEqual(response.data['marked_count'], 3)
        response = self.user1_client.get(NOTIFICATION_UNREAD_COUNT_URL)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        # created 2 notifications
        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.user1_tweet.id
        })
        comment = self.create_comment(self.user1, self.user1_tweet)
        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id
        })
        self.user2_client.post(COMMENT_URL, {
            'tweet_id': self.user1_tweet.id,
            'content': 'comment',
        })

        # test anonymous
        response = self.anonymous_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.status_code, 403)

        # test user2 list
        response = self.user2_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        # test user1 list
        response = self.user1_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.data['count'], 3)

        # test select notification
        notification = self.user1.notifications.first()
        notification.unread = False
        notification.save()
        response = self.user1_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.data['count'], 3)
        response = self.user1_client.get(NOTIFICATION_LIST_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)
        response = self.user1_client.get(NOTIFICATION_LIST_URL, {'unread': True})
        self.assertEqual(response.data['count'], 2)

    def test_update(self):
        # created 2 notifications
        self.user2_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.user1_tweet.id,
        })
        comment = self.create_comment(self.user1, self.user1_tweet)
        self.user2_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        # get 2 notifications
        first_notification = self.user1.notifications.first()
        second_notification = self.user1.notifications.exclude(
            id=first_notification.id,
        ).first()

        first_url = NOTIFICATION_UPDATE_URL.format(first_notification.id)
        second_url = NOTIFICATION_UPDATE_URL.format(second_notification.id)

        # test anonymous_client
        response = self.anonymous_client.put(first_url, {'unread': False})
        self.assertEqual(response.status_code, 403)

        # test get and post
        response = self.user1_client.get(second_url, {'unread': False})
        self.assertEqual(response.status_code, 405)
        response = self.user1_client.post(second_url, {'unread': False})
        self.assertEqual(response.status_code, 405)

        # test other user
        response = self.user2_client.put(second_url, {'unread': False})
        self.assertEqual(response.status_code, 404)
        second_notification.refresh_from_db()
        self.assertEqual(second_notification.unread, True)

        response = self.user1_client.put(first_url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        first_notification.refresh_from_db()
        second_notification.refresh_from_db()
        self.assertEqual(first_notification.unread, False)
        self.assertEqual(second_notification.unread, True)
