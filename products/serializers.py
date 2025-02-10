from rest_framework import serializers
from .models import (
    ProductType,
    Product,
    Wishlist,
    CartItems,
    Banner,
    ProductImage
)
from django.conf import settings
from backend.utils import validate_file_size1
from django.core.exceptions import ValidationError
import os
from backend.settings import NUMBER_OF_IMAGE_PER_PRODUCT

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'

    def validate_image(self, value):
        allowed_extensions = ["jpg", "jpeg", "png", "gif", "mp4"]
        if not any(value.name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError("Unsupported file format.")
        return value

class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = "__all__"
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(obj.image.url)
                if request
                else f"{settings.MEDIA_URL}{obj.image.url}"
            )
        return None


class ProductSerializer(serializers.ModelSerializer):
    product_type = serializers.PrimaryKeyRelatedField(
        queryset=ProductType.objects.all(),
        write_only=True,
    )
    product_type_detail = ProductTypeSerializer(source="product_type", read_only=True)
    images = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(obj.image.url)
                if request
                else f"{settings.MEDIA_URL}{obj.image.url}"
            )
        return None
    
    def get_images(self, obj):
        grp_data = ProductImage.objects.filter(product=obj)
        return ProductImageSerializer(
            grp_data, many=True, read_only=True, context=self.context
        ).data
    
    def to_representation(self, instance):
        # Get the default serialized data
        data = super().to_representation(instance)

        # Retrieve current user from context
        request = self.context.get("request")
        user = request.user if request else None

        # Check if the variant is in the user's wishlist
        if user and user.is_authenticated:
            is_favorit = Wishlist.objects.filter(
                user=user, product=instance
            ).exists()
        else:
            is_favorit = False

        # Add the is_favorit flag to the response
        data["is_favorit"] = is_favorit
        data["name"] = instance.name
        return data


class WishlistProductVariantSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = "__all__"

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(obj.image.url)
                if request
                else f"{settings.MEDIA_URL}{obj.image.url}"
            )
        return None

    def get_images(self, obj):
        grp_data = ProductImage.objects.filter(product=obj)
        return ProductImageSerializer(
            grp_data, many=True, read_only=True, context=self.context
        ).data
    
    def to_representation(self, instance):
        # Get the default serialized data
        data = super().to_representation(instance)

        # Retrieve current user from context
        request = self.context.get("request")
        user = request.user if request else None

        # Check if the variant is in the user's wishlist
        if user and user.is_authenticated:
            is_favorit = Wishlist.objects.filter(
                user=user, product=instance
            ).exists()
        else:
            is_favorit = False

        # Add the is_favorit flag to the response
        data["is_favorit"] = is_favorit
        data["name"] = instance.product.name
        return data


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = "__all__"


class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItems
        fields = "__all__"


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(obj.image.url)
                if request
                else f"{settings.MEDIA_URL}{obj.image.url}"
            )
        return None

    def validate_image(self, value):
        valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".mp4"]
        ext = os.path.splitext(value.name)[1]  # Extract the file extension
        if ext.lower() not in valid_extensions:
            # Raise custom error response
            raise ValidationError(
                {
                    "status": False,
                    "message": f"Unsupported file extension: {ext}. Allowed extensions are {', '.join(valid_extensions)}.",
                }
            )

        # Different size limits for different file types
        if ext.lower() in [".jpg", ".jpeg", ".png", ".gif"]:
            max_size = 5 * 1024 * 1024  # 5 MB for images
        elif ext.lower() == ".mp4":
            max_size = 50 * 1024 * 1024  # 60 MB for MP4 videos
        else:
            raise ValidationError(
                {"status": False, "message": "Unsupported file extension."}
            )

        # Validate file size
        validate_file_size1(value, max_size)
        return value
