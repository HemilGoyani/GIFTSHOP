from django.db import models
from backend.models import BaseModel
from users.models import User
from products.models import Product, ProductType
from phonenumber_field.modelfields import PhoneNumberField
from backend.utils import get_product_image_upload_path, validate_file_size
import uuid

class Order(BaseModel):
    """Stores the overall order for a user."""

    PENDING = 'PENDING'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELED = 'CANCELED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SHIPPED, 'Shipped'), 
        (DELIVERED, 'Delivered'),
        (CANCELED, 'Canceled'),
    ]

    order_number = models.CharField(max_length=100, unique=True, null=False, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="order_user")
    total_price = models.FloatField(default=0.0)
    total_gst = models.FloatField(default=0.0)
    is_deleted = models.BooleanField(default=False)

    # Razorpayment Integration
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

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

    def __str__(self):
        return f"Order Item {self.code} (Order {self.order.id})"
    
    class Meta:
        db_table = "order_item"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"