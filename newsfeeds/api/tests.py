from django.conf import settings
from friendships.models import Friendship
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
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
            self.create_tweet_with_newsfeed(user)

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
        tweet1 = self.create_tweet_with_newsfeed(user)
        newsfeed1 = NewsFeed.objects.filter(user=tweet1.user, tweet=tweet1).first()
        tweet2 = self.create_tweet_with_newsfeed(user)
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

        self.create_tweet_with_newsfeed(self.user1)
        self.create_newsfeed(self.user1, self.create_tweet_with_newsfeed(self.user2))

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

    def test_tweet_cache(self):
        tweet = self.create_tweet_with_newsfeed(self.user1, 'old content')

        response = self.user1_client.get(NEWSFEEDS_URL)
        result = response.data['results'][0]
        self.assertEqual(result['tweet']['content'], 'old content')

        tweet.content = 'new content'
        tweet.save()

        response = self.user1_client.get(NEWSFEEDS_URL)
        result = response.data['results'][0]
        self.assertEqual(result['tweet']['content'], 'new content')

    def _paginate_to_get_newsfeeds(self, client):
        response = client.get(NEWSFEEDS_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = results[-1]['created_at']
            response = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = 10

        users = [self.create_user(f'user {i}') for i in range(5)]

        newsfeeds = []
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(users[i % 5])
            newsfeed = self.create_newsfeed(self.user1, tweet)
            newsfeeds.append(newsfeed)
        newsfeeds.reverse()

        # only cached list_limit objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        self.assertEqual(cached_newsfeeds, newsfeeds[:list_limit])
        query_set = NewsFeed.objects.filter(user_id=self.user1.id)
        self.assertEqual(list(query_set), newsfeeds)

        results = self._paginate_to_get_newsfeeds(self.user1_client)
        self.assertEqual(len(results), len(newsfeeds))
        for i in range(len(results)):
            self.assertEqual(results[i]['id'], newsfeeds[i].id)

        # a followed user create a new tweet
        self.create_friendship(self.user1, self.user2)
        tweet = self.create_tweet(self.user2)
        NewsFeedService.fanout_to_followers(tweet)

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_newsfeeds(self.user1_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['tweet']['id'], tweet.id)
            for i in range(list_limit + page_size):
                self.assertEqual(results[i + 1]['id'], newsfeeds[i].id)

        _test_newsfeeds_after_new_feed_pushed()
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()
