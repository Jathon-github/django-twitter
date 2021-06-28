from friendships.models import Friendship
from rest_framework import status
from rest_framework.test import APIClient
from testing.testcases import TestCase
from utils.paginations import FriendshipPagination


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
        self.assertEqual(len(response.data['results']), 3)

        time0 = response.data['results'][0]['created_at']
        time1 = response.data['results'][1]['created_at']
        time2 = response.data['results'][2]['created_at']
        self.assertEqual(time0 > time1, True)
        self.assertEqual(time1 > time2, True)

        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'user1_following2'
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'user1_following1'
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
            'user1_following0'
        )

    def test_followers(self):
        user1_url = FOLLOWERS_URL.format(self.user1.id)

        response = self.anonymous_client.post(user1_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.anonymous_client.get(user1_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        time0 = response.data['results'][0]['created_at']
        time1 = response.data['results'][1]['created_at']
        self.assertEqual(time0 > time1, True)

        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'user1_follower1'
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'user1_follower0'
        )

    def test_followings_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size

        from_user = self.create_user('from_user')
        for i in range(page_size * 2):
            to_user = self.create_user(f'to_user_{i}')
            Friendship.objects.create(from_user=from_user, to_user=to_user)
            if to_user.id % 2 == 0:
                Friendship.objects.create(from_user=self.user1, to_user=to_user)

        url = FOLLOWINGS_URL.format(from_user.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # from_user has followed users with even id
        response = self.user1_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followers_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size

        to_user = self.create_user('to_user')
        for i in range(page_size * 2):
            from_user = self.create_user(f'from_user_{i}')
            Friendship.objects.create(from_user=from_user, to_user=to_user)
            if from_user.id % 2 == 0:
                Friendship.objects.create(from_user=self.user2, to_user=from_user)

        url = FOLLOWERS_URL.format(to_user.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # from_user has followed users with even id
        response = self.user2_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        response = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_results'], 2 * page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        response = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_results'], 2 * page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, 404)

        response = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), max_page_size)
        self.assertEqual(response.data['total_results'], 2 * page_size)
        self.assertEqual(response.data['page_number'], 1)

        response = self.anonymous_client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total_pages'], page_size)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
