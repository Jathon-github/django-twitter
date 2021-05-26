from django.contrib.auth.models import User
from rest_framework import serializers, exceptions


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')


class UserSerializerForTweet(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class UserSerializerForFriendship(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class UserSerializerForComment(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        if not User.objects.filter(username=attrs['username'].lower()).exists():
            raise exceptions.ValidationError({
                'username': 'User does not exist.'
            })
        attrs['username'] = attrs['username'].lower()
        return attrs


class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(min_length=6, max_length=20)
    password = serializers.CharField(min_length=6, max_length=20)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, attrs):
        if User.objects.filter(username=attrs['username'].lower()).exists():
            raise exceptions.ValidationError({
                'username': 'This username address has been occupied.'
            })
        if User.objects.filter(email=attrs['email'].lower()).exists():
            raise exceptions.ValidationError({
                'email': 'This email address has been occupied.'
            })
        return attrs

    def create(self, validated_data):
        username = validated_data['username'].lower()
        email = validated_data['email'].lower()
        password = validated_data['password']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        return user