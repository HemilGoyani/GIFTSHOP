from django.urls import path
from .views import (
    ProductTypeAPIView,
    ProductAPIView,
    WishlistView,
    CartAPIView,
    BannerAPIView,
    ProductImageUploadView,
    ProductImageDeleteView

)

urlpatterns = [
    # Product Type API
    path(
        "product-types/", ProductTypeAPIView.as_view(), name="product_type_list_create"
    ),
    path(
        "product-types/<int:pk>/",
        ProductTypeAPIView.as_view(),
        name="product_type_detail",
    ),
    # Product API
    path("", ProductAPIView.as_view(), name="product_list"),
    path("<int:pk>/", ProductAPIView.as_view(), name="product_detail"),
    # Product Wish List
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    # User Cart API
    path("cart/", CartAPIView.as_view(), name="cart-list"),
    path("cart/<int:cart_item_id>/", CartAPIView.as_view(), name="cart_item_detail"),
    # Get Banner API.
    path("banners/", BannerAPIView.as_view(), name="banner-list-create"),
    path(
        "banners/<int:pk>/",
        BannerAPIView.as_view(),
        name="banner-retrieve-update-delete",
    ),
    path('product-image/<int:product_id>/', ProductImageUploadView.as_view(), name='product-image-upload'),
    path('product-image-delete/<int:image_id>/', ProductImageDeleteView.as_view(), name='product-image-delete'),
]