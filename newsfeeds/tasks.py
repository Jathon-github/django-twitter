from celery import shared_task
from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from tweets.models import Tweet
from utils.time_constants import ONE_HOUR


@shared_task(time_limit=ONE_HOUR)
def fanout_to_followers(tweet_id):
    from newsfeeds.services import NewsFeedService

    tweet = Tweet.objects.get(id=tweet_id)
    newsfeeds = [
        NewsFeed(user_id=follower_id, tweet=tweet)
        for follower_id in FriendshipService.get_followers(tweet.user)
    ]
    newsfeeds.append(NewsFeed(user_id=tweet.user_id, tweet=tweet))
    NewsFeed.objects.bulk_create(newsfeeds)
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)
