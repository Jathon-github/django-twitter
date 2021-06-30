from testing.testcases import TestCase
from friendships.services import FriendshipService
from friendships.models import Friendship


class FriendshipServiceTests(TestCase):
    def setUp(self):
        self.clear_cache()

    def test_get_followings(self):
        from_user = self.create_user('from_user')
        to_user1 = self.create_user('to_user_1')
        to_user2 = self.create_user('to_user_2')

        to_users = FriendshipService.get_following_user_id_set(from_user.id)
        self.assertEqual(to_users, set())

        Friendship.objects.create(from_user=from_user, to_user=to_user1)
        Friendship.objects.create(from_user=from_user, to_user=to_user2)
        to_users = FriendshipService.get_following_user_id_set(from_user.id)
        self.assertEqual(to_users, {to_user1.id, to_user2.id})

        Friendship.objects.filter(from_user=from_user, to_user=to_user2).delete()
        to_users = FriendshipService.get_following_user_id_set(from_user.id)
        self.assertEqual(to_users, {to_user1.id})
