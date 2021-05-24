from testing.testcases import TestCase
from rest_framework.test import APIClient
from friendships.models import Friendship
from rest_framework import status


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


# Create your tests here.
class NewsFeedApiTest(TestCase):
    def setUp(self):
        self.user1 = self.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

        for i in range(2):
            follower = self.create_user(f'user1_follower{i}')
            Friendship.objects.create(from_user=follower, to_user=self.user1)

        for i in range(3):
            following = self.create_user(f'user1_following{i}')
            Friendship.objects.create(from_user=self.user1, to_user=following)

    def test_list(self):
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user1_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['newsfeeds']), 0)

        self.user1_client.post(POST_TWEETS_URL, {'content': 'user1_tweet'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)

        self.user1_client.post(FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(POST_TWEETS_URL, {'content': 'user2_tweet'})
        posted_tweet_id = response.data['id']
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)
