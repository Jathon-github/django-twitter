from testing.testcases import TestCase


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = self.create_user('user')
        self.tweet = self.create_tweet(user=self.user, content='tweet')
        self.comment = self.create_comment(self.user, self.tweet)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        self.create_like(self.user, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.create_like(self.user, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.create_like(self.create_user('other_user'), self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)
