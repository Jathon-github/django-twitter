from testing.testcases import TestCase
from accounts.models import UserProfile


class UserProfileTests(TestCase):
    def test_profile_property(self):
        user = self.create_user('user')
        self.assertEqual(UserProfile.objects.count(), 0)

        # create UserProfile
        user_profile = user.profile
        self.assertEqual(isinstance(user_profile, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)

        # use cached UserProfile
        user_profile = user.profile
        self.assertEqual(isinstance(user_profile, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)
