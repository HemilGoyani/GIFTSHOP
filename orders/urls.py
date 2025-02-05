from django.urls import path
from .views import OrderAPIView, CreateRazorpayOrder, VerifyPayment, InvoiceListView 

urlpatterns = [
    # Product Type API
    path('', OrderAPIView.as_view(), name='product_type_list_create'),
    path('<int:pk>/', OrderAPIView.as_view(), name='product_type_detail'),
    path('checkout-order/<int:order_id>/', CreateRazorpayOrder.as_view(), name='checkout_order'),
    path('verify-payment/', VerifyPayment.as_view(), name='verify_payment'),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
]