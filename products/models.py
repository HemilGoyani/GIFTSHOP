from django.db import models
from backend.models import BaseModel
from backend.utils import get_product_image_upload_path
from backend.utils import validate_file_size
from users.models import User
from django.core.validators import FileExtensionValidator


class ProductType(BaseModel):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    image = models.ImageField(
        upload_to="product-type/",
        blank=True,
        null=True,
        validators=[validate_file_size],
    )
    description = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Convert name to lowercase and strip spaces
        if self.name:
            self.name = self.name.strip().lower()
        super(ProductType, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(BaseModel):
    """Main product model to store common product attributes."""
    OUT_OF_STOCK = "OUT_OF_STOCK"
    IN_STOCK = "IN_STOCK"

    STATUS = [
        ("OUT_OF_STOCK", "OUT_OF_STOCK"),
        ("IN_STOCK", "IN_STOCK"),
    ]
    name = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, unique=True)
    product_type = models.ForeignKey(
        "ProductType", on_delete=models.PROTECT, related_name="product_type"
    )
    price = models.FloatField()
    status = models.CharField(max_length=255, choices=STATUS, default=OUT_OF_STOCK, null=True, blank=True)
    image = models.ImageField(
        upload_to=get_product_image_upload_path,
        blank=False,
        null=False,
        validators=[validate_file_size],
    )

    def __str__(self):
        return self.code

    class Meta:
        db_table = "product"
        verbose_name = "Product"


class Wishlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlisted_produc",
    )

    def __str__(self):
        return f"Wish list for {self.user.email} - {self.product.code}"


class ShoppingCart(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="shopping_cart"
    )

    def __str__(self):
        return f"Shopping Cart for {self.user.email}"


class CartItems(BaseModel):
    cart = models.ForeignKey(
        ShoppingCart,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="cart_items",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_product"
    )
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Cart list for {self.cart.user.email} - {self.product.code}"

    class Meta:
        db_table = "cart"


class Banner(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True, unique=True)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(
        upload_to="banners/",
        validators=[
            # Limit file types to .jpg, .jpeg, .png, .gif, and .mp4
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "gif", "mp4"]
            )
        ],
    )

    def __str__(self):
        return f"Banner {self.id}"