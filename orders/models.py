from django.db import models
from backend.models import BaseModel
from users.models import User
from products.models import Product, ProductType
from phonenumber_field.modelfields import PhoneNumberField
from backend.utils import get_product_image_upload_path, validate_file_size, get_order_upload_path
import uuid
from django.core.validators import FileExtensionValidator
from datetime import date


class Coupon(BaseModel):
    PERCENTAGE = 'PERCENTAGE'
    FIXED = 'FIXED'

    DISCOUNT_TYPES = [
        (PERCENTAGE, 'Percentage'),
        (FIXED, 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default=PERCENTAGE)
    discount_value = models.FloatField()
    max_discount = models.FloatField(null=True, blank=True)  # Maximum discount amount (optional)
    min_order_amount = models.FloatField(default=0.0)  # Minimum order value requirede
    valid_from = models.DateField()
    valid_to = models.DateField()

    def is_valid(self):
        today = date.today()
        return self.valid_from <= today <= self.valid_to and self.used_count < self.usage_limit

    def __str__(self):
        return f"{self.code} - {self.discount_type} ({self.discount_value})"

    class Meta:
        db_table = "coupon"
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"


class Order(BaseModel):
    """Stores the overall order for a user."""

    PLACED = 'PLACED'
    CONFIRMED = 'CONFIRMED'
    PACKAGING = 'PACKAGING'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (PLACED, 'Order Placed'),
        (CONFIRMED, 'Order Confirmed'),
        (PACKAGING, 'Product Packaging'),
        (SHIPPED, 'Product Shipped'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('ONLINE', 'Online Payment'),
        ('COD', 'Cash on Delivery'),
    ]

    order_number = models.CharField(max_length=100, unique=True, null=False, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PLACED)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="order_user")
    total_price = models.FloatField(default=0.0)
    total_gst = models.FloatField(default=0.0)
    is_deleted = models.BooleanField(default=False)

    # Payment related fields
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='ONLINE')
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    # Shiprocket specific fields
    cod_charges = models.FloatField(default=0.0)
    shiprocket_order_id = models.CharField(max_length=100, null=True, blank=True)
    shiprocket_shipment_id = models.CharField(max_length=100, null=True, blank=True)
    awb_code = models.CharField(max_length=100, null=True, blank=True)
    is_cod = models.BooleanField(default=False)

    # Add the Address details
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(
        verbose_name="Phone no.",
        help_text="Provide a number with country code (e.g. +12125552368).",
        null=True, 
        blank=True
    )
    state = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    pincode = models.CharField(max_length=200, null=True, blank=True)
    landmark = models.CharField(max_length=200, null=True, blank=True)

    # Order shiping data
    product_name = models.CharField(max_length=255, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    courier_service = models.CharField(max_length=255, blank=True, null=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    warehouse = models.CharField(max_length=255, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.FloatField(default=0.0)
    final_price = models.FloatField(default=0.0)
    
    def save(self, *args, **kwargs):
        # Auto-generate order number if not already set
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Order {self.id} by {self.user.email}"
    
    class Meta:
        db_table = "order"
        verbose_name = "Order"
        verbose_name_plural = "Orders"


class OrderItem(BaseModel):
    """Stores the items in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True)
    product_type = models.ForeignKey(
        ProductType, on_delete=models.PROTECT, related_name="order_product_type"
    )
    price = models.FloatField()
    image = models.ImageField(
        upload_to=get_product_image_upload_path,
        blank=False,
        null=False,
        validators=[validate_file_size],
    )
    quantity = models.IntegerField(default=1)
    url = models.URLField(max_length=1000, null=True, blank=True)
    user_image = models.FileField(
        upload_to=get_order_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png"]
            )
        ],
    ) 


    def __str__(self):
        return f"Order Item {self.code} (Order {self.order.id})"
    
    class Meta:
        db_table = "order_item"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.status} ({self.timestamp})"


class ProductReview(BaseModel):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='product_reviews', null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Review by {self.user.email} for {self.product.code} - Rating: {self.rating}"

    class Meta:
        db_table = "product_review"
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        unique_together = ('user', 'product', 'order_item')