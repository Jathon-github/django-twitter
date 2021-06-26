from tweets.models import TweetPhoto


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
