from accounts.models import UserProfile
from testing.testcases import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):
    def setUp(self):
        self.clear_cache()

        self.user = self.create_user(
            username='admin',
            email='admin@django.com',
            password='correct password',
        )

    def test_login(self):
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 405)

        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['username'], 'admin')

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@django.com',
            'password': 'any password',
        }

        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@django.com',
            'password': 'short',
        })
        self.assertEqual(response.status_code, 400)

        response = self.client.post(SIGNUP_URL, {
            'username': 'This username is very long',
            'email': 'someone@django.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        # test profile exists
        user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=user_id).first()
        self.assertNotEqual(profile, None)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)


class UserProfileApiTests(TestCase):
    def setUp(self):
        self.clear_cache()
        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')

    def test_update(self):
        user1_profile = self.user1.profile
        user1_profile.nickname = 'old nickname'
        user1_profile.save()
        url = USER_PROFILE_DETAIL_URL.format(user1_profile.id)

        # anonymous_client
        response = self.anonymous_client.put(url, {'nickname': 'new nickname'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'].code, 'not_authenticated')
        user1_profile.refresh_from_db()
        self.assertEqual(user1_profile.nickname, 'old nickname')

        # other user
        response = self.user2_client.put(url, {'nickname': 'new nickname'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'].code, 'permission_denied')
        user1_profile.refresh_from_db()
        self.assertEqual(user1_profile.nickname, 'old nickname')

        # update nickname
        response = self.user1_client.put(url, {'nickname': 'new nickname'})
        self.assertEqual(response.status_code, 200)
        user1_profile.refresh_from_db()
        self.assertEqual(user1_profile.nickname, 'new nickname')

        # update avatar
        response = self.user1_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='avatar.jpg',
                content='avatar image'.encode(),
                content_type='image/jpeg',
            ),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual('avatar' in response.data['avatar'], True)
        user1_profile.refresh_from_db()
        self.assertNotEqual(user1_profile.avatar, None)
