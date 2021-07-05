from django.conf import settings
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from django.conf import settings


class RedisHelper:
    @classmethod
    def _load_objects_to_cache(cls, key, query_set):
        conn = RedisClient.get_connection()

        serializer_list = []
        for obj in query_set[:settings.REDIS_LIST_LENGTH_LIMIT]:
            serializer = DjangoModelSerializer.serializer(obj)
            serializer_list.append(serializer)

        if serializer_list:
            conn.rpush(key, *serializer_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, key, query_set):
        conn = RedisClient.get_connection()

        if conn.exists(key):
            serializer_list = conn.lrange(key, 0, -1)
            objects = []
            for serializer in serializer_list:
                obj = DjangoModelSerializer.deserializer(serializer)
                objects.append(obj)
            return objects

        cls._load_objects_to_cache(key, query_set)
        return list(query_set)

    @classmethod
    def push_object(cls, key, tweet, query_set):
        conn = RedisClient.get_connection()

        if not conn.exists(key):
            cls._load_objects_to_cache(key, query_set)
            return

        serializer = DjangoModelSerializer.serializer(tweet)
        conn.lpush(key, serializer)
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)
