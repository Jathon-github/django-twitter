from testing.testcases import TestCase
from rest_framework.test import APIClient
from friendships.models import Friendship
from rest_framework import status


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


# Create your tests here.
class FriendshipApiTest(TestCase):
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

    def test_follow(self):
        user1_url = FOLLOW_URL.format(self.user1.id)
        user2_url = FOLLOW_URL.format(self.user2.id)

        response = self.anonymous_client.post(user2_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user1_client.get(user2_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.user2_client.post(user2_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.user1_client.post(user2_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['duplicate'], False)
        self.assertEqual(response.data['user']['id'], self.user2.id)

        response = self.user1_client.post(user2_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['duplicate'], True)

        count = Friendship.objects.count()
        response = self.user2_client.post(user1_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        user2_url = UNFOLLOW_URL.format(self.user2.id)

        response = self.anonymous_client.post(user2_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user1_client.get(user2_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        count = Friendship.objects.count()
        response = self.user1_client.post(user2_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)

        count = Friendship.objects.count()
        response = self.user1_client.post(user2_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        user1_url = FOLLOWINGS_URL.format(self.user1.id)

        response = self.anonymous_client.post(user1_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.anonymous_client.get(user1_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['followings']), 3)

        time0 = response.data['followings'][0]['created_at']
        time1 = response.data['followings'][1]['created_at']
        time2 = response.data['followings'][2]['created_at']
        self.assertEqual(time0 > time1, True)
        self.assertEqual(time1 > time2, True)

        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'user1_following2'
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'user1_following1'
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'user1_following0'
        )

    def test_followers(self):
        user1_url = FOLLOWERS_URL.format(self.user1.id)

        response = self.anonymous_client.post(user1_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.anonymous_client.get(user1_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['followers']), 2)

        time0 = response.data['followers'][0]['created_at']
        time1 = response.data['followers'][1]['created_at']
        self.assertEqual(time0 > time1, True)

        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'user1_follower1'
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'user1_follower0'
        )
