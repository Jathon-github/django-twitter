from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet
from tweets.models import TweetPhoto
from utils.pagination import EndlessPagination


TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TestApiTests(TestCase):
    def setUp(self):
        self.clear_cache()

        self.user1 = self.create_user('user1')
        self.tweets1 = [
            self.create_tweet_with_newsfeed(self.user1)
            for _ in range(3)
        ]
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2')
        self.tweets2 = [
            self.create_tweet_with_newsfeed(self.user2)
            for _ in range(2)
        ]

    def test_list_api(self):
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)

        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

        self.assertEqual(response.data['results'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweets2[0].id)

    def test_retrieve_api(self):
        response = self.anonymous_client.get(TWEET_RETRIEVE_API.format(-1))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        tweet = self.create_tweet_with_newsfeed(user=self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)

        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['tweet']['comments']), 0)

        self.create_comment(user=self.user1, tweet=tweet)
        self.create_comment(user=self.user2, tweet=tweet)
        self.create_comment(user=self.user2, tweet=self.create_tweet_with_newsfeed(user=self.user1))
        response = self.anonymous_client.get(url)
        self.assertEqual(len(response.data['tweet']['comments']), 2)

        # tweet 里包含用户的头像和昵称
        profile = self.user1.profile
        self.assertEqual(response.data['tweet']['user']['nickname'], profile.nickname)
        self.assertEqual(response.data['tweet']['user']['avatar_url'], None)

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

    def test_create_with_files(self):
        # test not has files
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'tweet content',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # test files is empty
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'tweet content',
            'files': [],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # test one file
        file = SimpleUploadedFile(
            name='test.jpg',
            content='test content'.encode(),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'tweet content',
            'files': [file],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        # test many files
        file1 = SimpleUploadedFile(
            name='test1.jpg',
            content='test1 content'.encode(),
            content_type='image/jpeg',
        )
        file2 = SimpleUploadedFile(
            name='test2.jpg',
            content='test2 content'.encode(),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'tweet content',
            'files': [file1, file2],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 3)

        # test retrieve and order
        retrieve_url = TWEET_RETRIEVE_API.format(response.data['id'])
        response = self.user1_client.get(retrieve_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('photo_urls' in response.data['tweet'], True)
        self.assertEqual(len(response.data['tweet']['photo_urls']), 2)
        self.assertEqual('test1' in response.data['tweet']['photo_urls'][0], True)
        self.assertEqual('test2' in response.data['tweet']['photo_urls'][1], True)

        # test TWEET_PHOTOS_UPLOAD_LIMIT
        files = [
            SimpleUploadedFile(
                name=f'test{i}.jpg',
                content=f'test{i} content'.encode(),
                content_type='image/jpeg',
            )
            for i in range(10)
        ]
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'content',
            'files': files,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TweetPhoto.objects.count(), 3)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        last_page_size = (page_size + 1) // 2

        user = self.create_user('user')
        for i in range(page_size + last_page_size):
            self.create_tweet_with_newsfeed(user)

        # hasn't created_at__gt any created_at__lt
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], True)
        first_time = response.data['results'][0]['created_at']
        last_time = response.data['results'][0]['created_at']

        for i in range(1, page_size):
            self.assertEqual(response.data['results'][i]['created_at'] < last_time, True)
            last_time = response.data['results'][i]['created_at']

        # has created_at__gt
        tweet1 = self.create_tweet_with_newsfeed(user)
        tweet2 = self.create_tweet_with_newsfeed(user)
        response = self.anonymous_client.get(TWEET_LIST_API, {
            'user_id': user.id,
            'created_at__gt': first_time,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(response.data['results'][0]['id'], tweet2.id)
        self.assertEqual(response.data['results'][1]['id'], tweet1.id)

        # has created_at__lt
        response = self.anonymous_client.get(TWEET_LIST_API, {
            'user_id': user.id,
            'created_at__lt': last_time,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), last_page_size)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(response.data['results'][0]['created_at'] < last_time, True)
