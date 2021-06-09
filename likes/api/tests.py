from testing.testcases import TestCase
from rest_framework import status


LIKE_BASE_URL = '/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'


class LikeApiTest(TestCase):
    def setUp(self):
        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')
        self.tweet = self.create_tweet(self.user1)
        self.comment = self.create_comment(user=self.user1, tweet=self.tweet)

    def test_tweet_like(self):
        data = {'content_type': 'tweet', 'object_id': self.tweet.id}

        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.user1_client.post(LIKE_BASE_URL,
                                          {'content_type': 'tweet'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.user1_client.post(LIKE_BASE_URL,
                                          {'object_id': self.tweet.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(self.tweet.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_comment_like(self):
        data = {'content_type': 'comment', 'object_id': self.comment.id}

        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.user1_client.post(LIKE_BASE_URL,
                                          {'content_type': 'coment',
                                           'object_id': self.comment.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content_type' in response.data['errors'], True)

        response = self.user1_client.post(LIKE_BASE_URL,
                                          {'content_type': 'comment',
                                           'object_id': -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('object_id' in response.data['errors'], True)

        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(self.comment.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(self.comment.like_set.count(), 2)

    def test_cancel(self):
        self.create_like(self.user1, self.tweet)
        self.create_like(self.user2, self.comment)
        self.assertEqual(self.tweet.like_set.count(), 1)
        self.assertEqual(self.comment.like_set.count(), 1)

        like_tweet_data = {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        }
        like_comment_data = {
            'content_type': 'comment',
            'object_id': self.comment.id,
        }

        response = self.anonymous_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user2_client.get(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.user1_client.post(LIKE_CANCEL_URL, {
            'content_type': 'twitter',
            'object_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('content_type' in response.data['errors'], True)

        response = self.user2_client.post(LIKE_CANCEL_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('object_id' in response.data['errors'], True)

        response = self.user2_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(self.tweet.like_set.count(), 1)
        self.assertEqual(self.comment.like_set.count(), 1)

        response = self.user1_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(self.tweet.like_set.count(), 1)
        self.assertEqual(self.comment.like_set.count(), 1)

        response = self.user1_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(self.tweet.like_set.count(), 0)
        self.assertEqual(self.comment.like_set.count(), 1)

        response = self.user2_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.tweet.like_set.count(), 0)
        self.assertEqual(self.comment.like_set.count(), 0)
