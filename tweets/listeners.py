def push_tweet_to_cache(sender, instance, **kwargs):
    from tweets.services import TweetService
    TweetService.push_cached_tweets(instance)
