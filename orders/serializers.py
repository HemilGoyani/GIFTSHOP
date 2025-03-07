from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, ProductReview, Coupon
from products.models import Product, CartItems
from products.serializers import ProductSerializer
from django.shortcuts import get_object_or_404
from users.models import User
from users.serializers import UserListSerializer
from django.conf import settings
from drf_extra_fields.fields import Base64ImageField

class OrderItemSerializerList(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)
    user_image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "url", "user_image"]
    
    def get_url(self, obj):
        """Returns the URL of the product associated with the order item."""
        return obj.url if obj.url else None

    def get_user_image(self, obj):
        if obj.user_image:
            request = self.context.get("request")
            return (
                request.build_absolute_uri(obj.user_image.url)
                if request
                else f"{settings.MEDIA_URL}{obj.user_image.url}"
            )
        return None


class OrderHistorySerializer(serializers.ModelSerializer):
    changed_by = UserListSerializer(read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = "__all__"


class OrderSerializerList(serializers.ModelSerializer):
    items = OrderItemSerializerList(many=True)
    user = UserListSerializer(read_only=True)
    history = OrderHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "user",
            "total_price",
            "total_gst",
            "items",
            "is_deleted",
            "name",
            "email",
            "phone_number",
            "state",
            "city",
            "address",
            "pincode",
            "landmark",
            "is_paid",
            "created_at",
            "updated_at",
            "history",
            "coupon",
            "discount_amount",
            "final_price"
        ]
        read_only_fields = (
            "user",
            "total_price",
            "is_deleted",
            "order_number",
            "is_paid",
            "history",
            "coupon",
            "discount_amount",
            "final_price"
        )


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
    )
    product_detail = ProductSerializer(source="product", read_only=True)
    url = serializers.URLField(required=False)
    user_image = Base64ImageField(required=False)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_detail", "quantity", "user_image", "url"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "user",
            "total_price",
            "total_gst",
            "items",
            "is_deleted",
            "name",
            "email",
            "phone_number",
            "state",
            "city",
            "address",
            "pincode",
            "landmark",
            "is_paid",
            "coupon",
            "discount_amount",
            "final_price"
        ]
        read_only_fields = (
            "user",
            "total_price",
            "is_deleted",
            "order_number",
            "is_paid",
            "coupon",
            "discount_amount",
            "final_price"
        )

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        total_price = 0
        total_gst = 0
        user = self.context["request"].user

        # Create the order
        order = Order.objects.create(**validated_data)
        user_cart_data = []
        # Calculate total price based on items and create OrderItem instances
        for item_data in items_data:
            # Extract the product ID instead of the product instance
            product = item_data.get("product", None)

            # Validate product belongs to product_color
            product = get_object_or_404(Product, id=product.id)
            quantity = item_data["quantity"]
            price = product.price
            total_price += quantity * price

            # Create the OrderItem instance
            OrderItem.objects.create(order=order, product=product, quantity=quantity, name=product.name, code=product.code, product_type=product.product_type, price=product.price, image=product.image, user_image=item_data.get('user_image', None), url=item_data.get('url', None))
            user_cart_data.append(product.id)

        # Update the total price in the order
        order.total_price = total_price
        order.total_gst = total_gst
        order.save()

        # delete cart data
        CartItems.objects.filter(cart__user=user, product__in=user_cart_data).delete()
        return order


class InvoiceListSerializer(serializers.ModelSerializer):
    items = OrderItemSerializerList(many=True)
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "user",
            "total_price",
            "total_gst",
            "items",
            "is_deleted",
            "name",
            "email",
            "phone_number",
            "state",
            "city",
            "address",
            "pincode",
            "landmark",
            "is_paid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "user",
            "total_price",
            "is_deleted",
            "order_number",
            "is_paid",
        )

    def get_user(self, obj):
        user_data = User.objects.filter(id=obj.user.id)
        return UserListSerializer(user_data, read_only=True, context=self.context).data


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["user_image", "url"]


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    def validate_status(self, value):
        """Ensure status is valid."""
        if value not in dict(Order.STATUS_CHOICES):
            raise serializers.ValidationError("Invalid status value.")
        return value


class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    order_item = serializers.PrimaryKeyRelatedField(queryset=OrderItem.objects.all())

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'product', 'order_item', 'rating', 'review_text']
        read_only_fields = ['id', 'user']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate(self, data):
        """
        Custom validation to ensure:
        1. User has ordered the product in the specified order_item.
        2. The order status is 'DELIVERED'.
        3. The review is not already submitted for this order item by this user.
        """
        order_item = data['order_item']
        product = data['product']
        user = self.context['request'].user  # Get user from request context

        if order_item.product != product:
            raise serializers.ValidationError("The selected order item does not correspond to the selected product.")

        order = order_item.order
        if order.user != user:
            raise serializers.ValidationError("You are not authorized to review products in this order.")

        if order.status != Order.DELIVERED:
            raise serializers.ValidationError("You can only review products after the order is delivered.")

        # Check if a review already exists for this order item by this user
        if ProductReview.objects.filter(user=user, order_item=order_item).exists():
            raise serializers.ValidationError("You have already submitted a review for this product in this order.")

        return data

    def create(self, validated_data):
        """Override create to automatically set the user from the request."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UpdateProductReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductReview
        fields = ['id', 'rating', 'review_text']


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'