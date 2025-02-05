import os
import uuid
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

def validate_file_size(value):
    filesize = value.size
    if filesize >= 1024 * 1024 * settings.MAX_FILE_SIZE:
        raise ValidationError(
            f"Image file size should be less than {settings.MAX_FILE_SIZE}MB"
        )


def get_product_image_upload_path(instance, filename):
    # Use the product's ID and color to create a unique path
    return f"product/images/{filename}"


def superuser_required(func):
    """ Custom decorator to ensure that only superusers can access the view. """
    @wraps(func)
    def wrapped_view(self, request, *args, **kwargs):
        # Apply the IsAuthenticated permission
        permission = IsAuthenticated()
        if not permission.has_permission(request, self):
            return Response({"status": False, "message": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if the user is a superuser
        if not request.user.is_superuser:
            return Response({"status": False, "message": "Only superusers can perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        # Proceed to the view function if the user is authenticated and a superuser
        return func(self, request, *args, **kwargs)

    return wrapped_view


def validate_file_size1(value, max_size):
    """Custom file size validator to enforce maximum file size"""
    if value.size > max_size:
        raise ValidationError(f"File size exceeds the {max_size // (1024 * 1024)} MB limit.")


def serializers_error(serializer):
    if serializer:
        for field, errors in serializer.errors.items():
            field_name = field.replace('_', ' ').title()
            error_message = errors[0].replace("This", "")
            full_message = f"{field_name} {error_message}"
            return full_message
    return "Something went wrong!"