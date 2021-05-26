from testing.testcases import TestCase


# Create your tests here.
class CommentModelTest(TestCase):
    def test_comment(self):
        user = self.create_user('user')
        tweet = self.create_tweet(user=user, content='tweet')
        comment = self.create_comment(user, tweet)
        self.assertNotEqual(comment.__str__(), None)
