from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from django.conf import settings


class RedisHelper:
    @classmethod
    def get_count_key(cls, instance, attr):
        return f'{instance.__class__.__name__}.{attr}:{instance.id}'

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

    @classmethod
    def incr_count(cls, instance, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(instance, attr)
        if not conn.exists(key):
            instance.refresh_from_db()
            conn.set(key, getattr(instance, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(instance, attr)
        return conn.incr(key)

    @classmethod
    def decr_count(cls, instance, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(instance, attr)
        if not conn.exists(key):
            instance.refresh_from_db()
            conn.set(key, getattr(instance, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(instance, attr)
        return conn.decr(key)

    @classmethod
    def get_count(cls, instance, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(instance, attr)
        if not conn.exists(key):
            instance.refresh_from_db()
            conn.set(key, getattr(instance, attr))
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
            return int(getattr(instance, attr))
        return int(conn.get(key))
