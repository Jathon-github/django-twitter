from django.core import serializers
from utils.json_encoder import JSONEncoder


class DjangoModelSerializer:
    @classmethod
    def serializer(cls, instance):
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserializer(cls, serialized_data):
        return list(serializers.deserialize('json', serialized_data))[0].object
