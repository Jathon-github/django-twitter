from friendships.models import Friendship


class FriendshipService:
    @classmethod
    def get_followers(cls, user):
        friendships = Friendship.objects.filter(to_user=user)
        return [friendship.from_user_id for friendship in friendships]
