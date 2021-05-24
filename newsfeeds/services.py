from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed


class NewsFeedService:
    @classmethod
    def fanout_to_followers(cls, tweet):
        newsfeeds = [
            NewsFeed(user_id=follower_id, tweet=tweet)
            for follower_id in FriendshipService.get_followers(tweet.user)
        ]
        newsfeeds.append(NewsFeed(user_id=tweet.user_id, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)
