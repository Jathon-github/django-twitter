from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedService:
    @classmethod
    def fanout_to_followers(cls, tweet):
        newsfeeds = [
            NewsFeed(user_id=follower_id, tweet=tweet)
            for follower_id in FriendshipService.get_followers(tweet.user)
        ]
        newsfeeds.append(NewsFeed(user_id=tweet.user_id, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)
        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        query_set = NewsFeed.objects.filter(user_id=user_id)
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, query_set)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        query_set = NewsFeed.objects.filter(user_id=newsfeed.user_id)
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        return RedisHelper.push_object(key, newsfeed, query_set)
