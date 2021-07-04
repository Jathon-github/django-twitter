from tweets.models import Tweet, TweetPhoto
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis_helper import RedisHelper


class TweetService:
    @classmethod
    def create_photos_from_files(cls, tweet, files):
        photos = [
            TweetPhoto(
                tweet=tweet,
                user=tweet.user,
                file=photo,
                order=order,
            )
            for order, photo in enumerate(files)
        ]
        TweetPhoto.objects.bulk_create(photos)

    @classmethod
    def get_cached_tweets(cls, user_id):
        query_set = Tweet.objects.filter(user_id=user_id)
        key = USER_TWEETS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, query_set)

    @classmethod
    def push_tweet_to_cache(cls, tweet):
        query_set = Tweet.objects.filter(user_id=tweet.user_id)
        key = USER_TWEETS_PATTERN.format(user_id=tweet.user_id)
        return RedisHelper.push_object(key, tweet, query_set)
