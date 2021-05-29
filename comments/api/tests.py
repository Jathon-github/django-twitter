from testing.testcases import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from comments.models import Comment


COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'


class CommentApiTest(TestCase):
    def setUp(self):
        self.user1 = self.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

        self.tweet = self.create_tweet(self.user1)

    def test_list(self):
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 0)

        self.create_comment(self.user1, self.tweet, 'first comment')
        self.create_comment(self.user2, self.tweet, 'second comment')
        self.create_comment(self.user2, self.create_tweet(self.user2), 'third comment')

        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], 'first comment')
        self.assertEqual(response.data['comments'][1]['content'], 'second comment')

        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.user1.id,
        })
        self.assertEqual(len(response.data['comments']), 2)

    def test_create(self):
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # response = self.user1_client.get(COMMENT_URL)
        # self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

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

    def test_destroy(self):
        comment = self.create_comment(self.user1, self.tweet)
        url = COMMENT_DETAIL_URL.format(comment.id)

        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user2_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        count = Comment.objects.count()
        response = self.user1_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.count(), count - 1)
