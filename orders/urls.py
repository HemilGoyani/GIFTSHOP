from django.urls import path
from .views import OrderAPIView, CreateRazorpayOrder, VerifyPayment, InvoiceListView, OrderItemUpdateAPIView, OrderStatusUpdateView, OrderStatusHistoryAPIView, CreateProductReviewAPIView, ApplyCouponView, CouponAPIView, CODPayment

urlpatterns = [
    # Product Type API
    path('', OrderAPIView.as_view(), name='product_type_list_create'),
    path('<int:pk>/', OrderAPIView.as_view(), name='product_type_detail'),
    path('checkout-order/<int:order_id>/', CreateRazorpayOrder.as_view(), name='checkout_order'),
    path('cod-checkout-order/<int:order_id>/', CODPayment.as_view(), name='cod-checkout_order'),
    path('verify-payment/', VerifyPayment.as_view(), name='verify_payment'),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path("order-item/<int:pk>/", OrderItemUpdateAPIView.as_view(), name="order-item-update"),
    path('update-status/<int:order_id>/', OrderStatusUpdateView.as_view(), name='update_order_status'),
    path("order-history/", OrderStatusHistoryAPIView.as_view(), name="order-history"),
    path("order-history/<int:order_id>/", OrderStatusHistoryAPIView.as_view(), name="order-history-detail"),
    path('reviews/', CreateProductReviewAPIView.as_view(), name='create-review'),
    path('reviews/<int:review_id>/', CreateProductReviewAPIView.as_view(), name='update-delete-review'),
    path('apply-coupon/<int:order_id>/', ApplyCouponView.as_view(), name='apply_coupon'),
    path('coupons/', CouponAPIView.as_view(), name='coupon-list-create'),
    path('coupons/<int:pk>/', CouponAPIView.as_view(), name='coupon-detail')
]