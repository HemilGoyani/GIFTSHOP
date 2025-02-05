from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import (
    OrderSerializer,
    OrderSerializerList,
    InvoiceListSerializer,
)
from django.shortcuts import get_object_or_404
from django.conf import settings
import razorpay
from backend.utils import serializers_error


class OrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of orders or a single order for the authenticated user.
        """
        order_id = kwargs.get("pk")
        is_paid = self.request.query_params.get("is_paid", None)
        
        if is_paid and is_paid not in ["True", "False"]:
            return Response(
                {"status": False, "message": "Invalid filter type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order_id:
            order = get_object_or_404(Order, pk=order_id, user=request.user)
            serializer = OrderSerializerList(order, context={"request": request})
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Order arrived successfully.",
                },
                status=status.HTTP_200_OK,
            )

        if self.request.user.is_site_admin:
            orders = Order.objects.all()
            if is_paid:
                orders = orders.filter(is_paid=is_paid)

            orders = orders.order_by("-id")

        else:
            orders = Order.objects.filter(user=request.user)
            if is_paid:
                orders = orders.filter(is_paid=is_paid)

            orders = orders.order_by("-id")

        serializer = OrderSerializerList(orders, many=True, context={"request": request})
        return Response(
            {
                "status": True,
                "data": serializer.data,
                "message": "Order arrived successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        """
        Create a new order for the authenticated user.
        """
        # Pass the request context to the serializer
        serializer = OrderSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(
                user=self.request.user,
                created_by=self.request.user,
                updated_by=self.request.user,
            )
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Order created successfully.",
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

    def delete(self, request, *args, **kwargs):
        """
        Delete an existing order for the authenticated user.
        """
        order = Order.objects.filter(
            id=kwargs.get("pk"), user=self.request.user
        ).first()
        if not order:
            return Response(
                {"status": False, "message": "Order not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.is_deleted = True
        order.save()
        return Response(
            {"status": True, "message": "Order deleted successfully."},
            status=status.HTTP_200_OK,
        )


class CreateRazorpayOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # Get order details from your system
        name = request.data.get("name")
        email = request.data.get("email")
        phone_number = request.data.get("phone_number")
        state = request.data.get("state")
        city = request.data.get("city")
        address = request.data.get("address")
        pincode = request.data.get("pincode")
        
        if not all([order_id, name, email, phone_number, state, city, address, pincode]):
            return Response(
                {"status": False, "message": "Please fill all details properly."},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return Response(
                {"status": False, "message": "Order not found."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not order.is_paid:

            # Razorpay client initialization
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            # GET THE ONLY TOKEN PAYMENT FOR 30% PERCENT
            amount = order.total_price

            # Create a Razorpay order
            razorpay_order_data = {
                "amount": int(amount * 100),  # amount in paise (INR)
                "currency": "INR",
                "payment_capture": 1,  # automatic capture after payment
                "receipt": f"order_{order.id}",
            }

            try:
                razorpay_order = client.order.create(data=razorpay_order_data)
                order.razorpay_order_id = razorpay_order["id"]

                # Save address details
                order.name = name
                order.email = email
                order.phone_number = phone_number
                order.state = state
                order.city = city
                order.address = address
                order.pincode = pincode
                order.landmark = request.data.get("landmark")

                # Save changes
                order.created_by = self.request.user
                order.updated_by = self.request.user
                order.save()

                # Send order details to the frontend
                return Response(
                    {
                        "status": True,
                        "razorpay_order_id": razorpay_order["id"],
                        "amount": razorpay_order_data["amount"],
                        "currency": razorpay_order_data["currency"],
                        "order_id": order.id,
                        "message": "Order payment created successfully.",
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception as e:
                return Response(
                    {"status": False, "message": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(
                {
                    "status": False,
                    "message": "Payment Approved request time expire, please send payment request again!",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class VerifyPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_signature = request.data.get("razorpay_signature")

        # Verify the order exists
        order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()
        if not order:
            return Response(
                {"status": False, "message": "Payment order not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Proceed to verify the payment signature
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            # Mark the order as paid
            order.razorpay_payment_id = razorpay_payment_id
            order.is_paid = True
            order.created_by = self.request.user
            order.updated_by = self.request.user
            order.save()

            return Response(
                {"status": True, "message": "Payment Successfully."},
                status=status.HTTP_200_OK,
            )

        except razorpay.errors.SignatureVerificationError:
            return Response(
                {"status": False, "message": "Payment verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InvoiceListView(generics.ListAPIView):
    """
    API to list all orders with invoice details.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceListSerializer

    def get_queryset(self):
        # Filter orders for the authenticated user
        return Order.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        # Use the default list method, but customize the response
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "status": True,
                "data": serializer.data,
                "message": "Invoice data arrived successfully.",
            },
            status=status.HTTP_200_OK,
        )