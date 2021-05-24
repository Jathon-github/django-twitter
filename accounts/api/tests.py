from testing.testcases import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User


LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountApiTests(TestCase):
    def setUp(self):
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
        self.assertEqual(response.data['user']['email'], 'admin@django.com')

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

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)
