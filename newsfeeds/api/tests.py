from friendships.models import Friendship
from newsfeeds.models import NewsFeed
from rest_framework import status
from rest_framework.test import APIClient
from testing.testcases import TestCase
from utils.pagination import EndlessPagination


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTest(TestCase):
    def setUp(self):
        self.clear_cache()

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
        self.assertEqual(len(response.data['results']), 0)

        self.user1_client.post(POST_TWEETS_URL, {'content': 'user1_tweet'})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)

        self.user1_client.post(FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(POST_TWEETS_URL, {'content': 'user2_tweet'})
        posted_tweet_id = response.data['id']
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        last_page_size = (page_size + 1) // 2

        user, user_client = self.create_user_and_client('user')
        for _ in range(page_size + last_page_size):
            self.create_tweet(user)

        # hasn't created_at__gt any created_at__lt
        response = user_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], True)
        first_time = response.data['results'][0]['created_at']
        last_time = response.data['results'][0]['created_at']

        for i in range(1, page_size):
            self.assertEqual(
                response.data['results'][i]['created_at'] < last_time, True)
            last_time = response.data['results'][i]['created_at']

        # has created_at__gt
        response = user_client.get(NEWSFEEDS_URL, {
            'created_at__gt': first_time,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)
        tweet1 = self.create_tweet(user)
        newsfeed1 = NewsFeed.objects.filter(user=tweet1.user, tweet=tweet1).first()
        tweet2 = self.create_tweet(user)
        newsfeed2 = NewsFeed.objects.filter(user=tweet2.user, tweet=tweet2).first()
        response = user_client.get(NEWSFEEDS_URL, {
            'created_at__gt': first_time,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(response.data['results'][0]['id'], newsfeed2.id)
        self.assertEqual(response.data['results'][1]['id'], newsfeed1.id)

        # has created_at__lt
        response = user_client.get(NEWSFEEDS_URL, {
            'created_at__lt': last_time,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), last_page_size)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(response.data['results'][0]['created_at'] < last_time, True)

    def test_user_cache(self):
        profile = self.user1.profile
        profile.nickname = 'old_nickname'
        profile.save()

        self.create_tweet(self.user1)
        self.create_newsfeed(self.user1, self.create_tweet(self.user2))

        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user2')
        self.assertEqual(results[1]['tweet']['user']['nickname'], 'old_nickname')

        profile.nickname = 'new_nickname'
        profile.save()
        self.user2.username = 'new_username'
        self.user2.save()

        response = self.user1_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(results[0]['tweet']['user']['username'], 'new_username')
        self.assertEqual(results[1]['tweet']['user']['nickname'], 'new_nickname')
