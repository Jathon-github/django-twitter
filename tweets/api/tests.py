from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet

TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'

class TestApiTests(TestCase):
    def setUp(self):
        self.user1 = self.create_user('user1')
        self.tweets1 = [
            self.create_tweet(self.user1)
            for _ in range(3)
        ]
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2')
        self.tweets2 = [
            self.create_tweet(self.user2)
            for _ in range(2)
        ]

    def test_list_api(self):
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 3)

        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 2)

        self.assertEqual(response.data['tweets'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['tweets'][1]['id'], self.tweets2[0].id)

    def test_create_api(self):
        response = self.anonymous_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(TWEET_CREATE_API, {'content': 'short'})
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(TWEET_CREATE_API, {'content': 'long' * 256})
        self.assertEqual(response.status_code, 400)

        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'Hello World',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count + 1)