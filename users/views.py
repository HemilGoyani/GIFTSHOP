from django.contrib.auth import authenticate
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializers,
    UserListSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
    PasswordResetRequestSerializer,
    GoogleSocialAuthSerializer,
    ContactUsSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from backend.utils import serializers_error
import re


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Save the user
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            tokens = {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }

            return Response(
                {
                    "status": True,
                    "message": "User created successfully",
                    "user": serializer.data,
                    **tokens,  # Include tokens in the response
                },
                status=status.HTTP_201_CREATED,
            )

        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserLoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializers

    def post(self, request):
        phone_number = request.data.get("phone_number", None)
        email = request.data.get("email", None)
        password = request.data.get("password", None)

        # Ensure either phone number or email is provided
        if not phone_number and not email:
            return Response(
                {
                    "status": False,
                    "message": "Either phone number or email is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not password:
            return Response(
                {"status": False, "message": "Please enter your password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for the provided contact method (phone or email)
        user = None
        if phone_number:
            user = User.objects.filter(phone_number__iexact=phone_number).first()
        elif email:
            user = User.objects.filter(email__iexact=email).first()

        # Verify Password
        if user:
            VerifyUser = authenticate(request, username=user.email, password=password)
            if VerifyUser:
                user_data = UserProfileSerializer(user).data
                return Response(
                    {
                        "detail": get_tokens_for_user(user),
                        "user": user_data,
                        "status": True,
                        "message": "Login successfully!.",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            else:
                return Response(
                    {"status": False, "message": "Invalid login credentials."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"status": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserListView(generics.ListAPIView):
    """API view to retrieve list of users, accessible only by admin users."""

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]


class PasswordValidatorMixin:
    def validate_password(self, password):
        """Validates password complexity."""
        if len(password) < 8:
            return Response(
                {
                    "status": False,
                    "message": "Password must be at least 8 characters long.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r"\d", password):
            return Response(
                {
                    "status": False,
                    "message": "Password must contain at least one digit.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r"[A-Z]", password):
            return Response(
                {
                    "status": False,
                    "message": "Password must contain at least one uppercase letter.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r"[\W_]", password):
            return Response(
                {
                    "status": False,
                    "message": "Password must contain at least one special character.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return password


class PasswordChangeView(generics.UpdateAPIView, PasswordValidatorMixin):
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_new_password = request.data.get("confirm_new_password")

        # Validate old password
        if not user.check_password(old_password):
            return Response(
                {"status": False, "message": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate new password and confirm new password match
        if new_password != confirm_new_password:
            return Response(
                {
                    "status": False,
                    "message": "New password and confirm new password do not match.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate new password complexity
        try:
            self.validate_password(
                new_password
            )  # This is from the PasswordValidatorMixin
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        # Set the new password and save the user
        user.set_password(new_password)
        user.save()

        return Response(
            {"status": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()

        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            if user.is_site_admin:
                reset_link = f"{settings.FRONTEND_DOMAIN}/v1/password-reset-confirm/{uid}/{token}/"
            else:
                reset_link = f"{settings.FRONTEND_DOMAIN}/reset-password/{uid}/{token}/"

            # Send the email
            subject = "Password Reset Request"
            msg_plain = render_to_string(
                "email.txt", {"reset_link": reset_link, "email": user.email}
            )
            email_template = render_to_string(
                "password_reset_email.html",
                {"reset_link": reset_link, "email": user.email},
            )
            send_mail(
                subject,
                msg_plain,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=email_template,
            )

            return Response(
                {"status": True, "message": "Password reset email sent."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": False, "message": "User with this email does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PasswordResetConfirmView(GenericAPIView, PasswordValidatorMixin):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        uidb64 = kwargs.get("uidb64")
        token = kwargs.get("token")

        # Decode the UID and retrieve the user
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"status": False, "message": "Invalid reset token or user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user is not None:
            # Check if the token is valid
            is_token_valid = default_token_generator.check_token(user, token)
            if is_token_valid:
                # Manually validate the new password and confirm new password
                new_password = request.data.get("new_password")
                confirm_new_password = request.data.get("confirm_new_password")

                # Validate if passwords match
                if new_password != confirm_new_password:
                    return Response(
                        {"status": False, "message": "Passwords do not match."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Validate password complexity
                try:
                    self.validate_password(new_password)
                except Exception as e:
                    return Response(
                        {"status": False, "message": str(e)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Set the new password and save the user
                user.set_password(new_password)
                user.auth_provider=User.EMAIL
                user.save()

                return Response(
                    {
                        "status": True,
                        "message": "Password has been reset successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": False, "message": "Invalid or expired token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"status": False, "message": "Invalid reset token or user."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    User = get_user_model()
    queryset = User.objects.all()  # Provide a default queryset

    def delete(self, request, *args, **kwargs):
        try:
            # Retrieve the user to be deleted
            user_to_delete = User.objects.filter(pk=kwargs.get("pk")).first()

            # Restrict non-admin users from deleting other users
            if not request.user.is_superuser and request.user.pk != user_to_delete.pk:
                return Response(
                    {
                        "status": False,
                        "message": "You do not have permission to delete this user.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Delete the user
            user_to_delete.delete()
            return Response(
                {"status": True, "message": "User deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"status": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Fetch the user's profile
        return self.request.user

    def put(self, request, *args, **kwargs):
        try:
            # Update the user profile using the serializer
            return self._create_response(request, *args, **kwargs)
        except Exception as e:
            # Catch validation errors and return a custom response
            return Response(
                {
                    "status": False,
                    "message": str(e),  # The message from the ValidationError
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def patch(self, request, *args, **kwargs):
        try:
            # Partially update the user profile
            return self._create_response(request, *args, **kwargs)
        except Exception as e:
            # Catch validation errors and return a custom response
            return Response(
                {
                    "status": False,
                    "message": str(e),  # The message from the ValidationError
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _create_response(self, request, *args, **kwargs):
        # Call the update or partial_update methods
        response = (
            super().update(request, *args, **kwargs)
            if request.method == "PUT"
            else super().partial_update(request, *args, **kwargs)
        )

        # You can access the validated data in the response and format it with a message
        data = response.data
        message = (
            "Profile updated successfully"
            if request.method == "PUT"
            else "Profile partially updated successfully"
        )

        return Response(
            {"status": True, "data": data, "message": message},
            status=status.HTTP_200_OK,
        )


class GoogleSocialAuthView(GenericAPIView):
    serializer_class = GoogleSocialAuthSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(
                raise_exception=True
            )  # This will raise a ValidationError if invalid
            data = serializer.validated_data["auth_token"]
            return Response(data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            # Return a custom response when the token is invalid or any other validation errors
            return Response(
                {
                    "status": False,
                    "message": str(e),  # The validation error message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            # Handle authentication failure due to invalid Google credentials
            return Response(
                {
                    "status": False,
                    "message": str(
                        e
                    ),  # The custom error message for failed authentication
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except Exception as e:
            # General exception handler for any other errors that may occur
            return Response(
                {
                    "status": False,
                    "message": "An unexpected error occurred: " + str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ContactUsAPIView(APIView):
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            first_name = serializer.validated_data["first_name"]
            last_name = serializer.validated_data["last_name"]
            email = serializer.validated_data["email"]
            phone_number = serializer.validated_data.get("phone_number", "Not provided")
            message = serializer.validated_data["message"]

            # Construct the email message
            subject = f"New Contact Us Message from {first_name} {last_name}"
            admin_message = (
                f"New contact request received:\n\n"
                f"Name: {first_name} {last_name}\n"
                f"Email: {email}\n"
                f"Phone Number: {phone_number}\n"
                f"Message:\n{message}"
            )

            try:
                send_mail(
                    subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACTUS_EMAIL],
                    fail_silently=False,
                )
                return Response(
                    {"status": True, "message": "Contact request sent successfully!"},
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {
                        "status": False,
                        "message": "Failed to send email. Please try again later.",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )