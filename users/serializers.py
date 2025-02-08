from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import User
from .register import register_social_user
from rest_framework.exceptions import AuthenticationFailed
from . import google
import os


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'first_name', 'last_name', 'gender', 'city', 'address', 'image', 'password']

    # Image validation
    def validate_image(self, value):
        # List of allowed file extensions
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        
        # Get the file extension of the uploaded image
        ext = os.path.splitext(value.name)[1].lower()  # Extract the file extension
        
        # Check if the file extension is valid
        if ext not in valid_extensions:
            raise ValidationError(f'Unsupported file extension "{ext}". Allowed extensions are: {", ".join(valid_extensions)}.')
        return value

    def create(self, validated_data):
        # Create the user instance
        user = User(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            gender=validated_data['gender'],
            city=validated_data.get('city', ''),
            address=validated_data.get('address', ''),
            image=validated_data.get('image', None),
        )
        # Set the user's password
        user.set_password(validated_data['password'])
        user.save()
        return user


class LoginSerializers(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "phone_number",
            "password",
        ]

    def create(self, validated_data):
        return super(LoginSerializers, self).create(validated_data)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'first_name', 'last_name', 'gender']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'gender', 'city', 'address', 'image']

    def validate_image(self, value):
        # List of allowed file extensions
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        
        # Get the file extension of the uploaded image
        ext = os.path.splitext(value.name)[1].lower()  # Extract the file extension
        
        # Check if the file extension is valid
        if ext not in valid_extensions:
            raise ValidationError(f'Unsupported file extension "{ext}". Allowed extensions are: {", ".join(valid_extensions)}.')
        return value

    def update(self, instance, validated_data):
        # If a new image is provided, delete the old image
        if 'image' in validated_data and instance.image:
            instance.image.delete(save=False)  # Delete the old image from storage
        return super().update(instance, validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

    def validate_auth_token(self, auth_token):
        user_data = google.Google.validate(auth_token)
        try:
            user_data['sub']
        except:
            raise serializers.ValidationError(
                'The token is invalid or expired. Please login again.'
            )

        if user_data['aud'] != os.environ.get('GOOGLE_CLIENT_ID'):

            raise AuthenticationFailed('oops, who are you?')

        user_id = user_data['sub']
        email = user_data['email']
        name = user_data['name']
        provider = 'GOOGLE'

        return register_social_user(
            provider=provider, user_id=user_id, email=email, name=name)


class ContactUsSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20, required=False)
    message = serializers.CharField()