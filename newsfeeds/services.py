from newsfeeds.models import NewsFeed
from newsfeeds.tasks import fanout_to_followers
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedService:
    @classmethod
    def fanout_to_followers(cls, tweet):
        fanout_to_followers.delay(tweet.id)

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
