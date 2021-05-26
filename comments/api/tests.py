from testing.testcases import TestCase
from rest_framework.test import APIClient
from rest_framework import status


COMMENT_URL = '/api/comments/'


class CommentApiTest(TestCase):
    def setUp(self):
        self.user1 = self.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

        self.tweet = self.create_tweet(self.user1)

    def test_create(self):
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user1_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.user1_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.user1_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content' in response.data['errors'], True)

        response = self.user1_client.post(COMMENT_URL, {'content': 'comment'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('tweet_id' in response.data['errors'], True)

        response = self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': ' ' * 128,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content' in response.data['errors'], True)

        response = self.user1_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'comment',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
