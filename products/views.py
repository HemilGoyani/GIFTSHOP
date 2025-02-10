from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import (
    ProductType,
    Product,
    Wishlist,
    ShoppingCart,
    CartItems,
    Banner,
    ProductImage,
)
from .serializers import (
    ProductTypeSerializer,
    ProductSerializer,
    WishlistSerializer,
    CartSerializer,
    BannerSerializer,
    ProductImageSerializer,
)
from backend.utils import superuser_required, serializers_error
from django.shortcuts import get_object_or_404
from django.db.models import ProtectedError


# ProductType CRUD API View
class ProductTypeAPIView(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                product_type = ProductType.objects.get(pk=pk)
                serializer = ProductTypeSerializer(
                    product_type, context={"request": request}
                )
                return Response(
                    {
                        "status": True,
                        "data": serializer.data,
                        "message": "Product Type retrieved successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
            except ProductType.DoesNotExist:
                return Response(
                    {"status": False, "message": "ProductType not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            product_types = ProductType.objects.all()
            serializer = ProductTypeSerializer(
                product_types, context={"request": request}, many=True
            )
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product Type retrieved successfully.",
                },
                status=status.HTTP_200_OK,
            )

    @superuser_required
    def post(self, request):
        serializer = ProductTypeSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save(
                    created_by=self.request.user, updated_by=self.request.user
                )
                return Response(
                    {
                        "status": True,
                        "data": serializer.data,
                        "message": "Product type created successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                if "product_producttype_name_key" in str(e):
                    return Response(
                        {
                            "status": False,
                            "message": "ProductType name already exists.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(
                    {
                        "status": False,
                        "message": "An error occurred while saving the product type.",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @superuser_required
    def put(self, request, pk=None):
        try:
            product_type = ProductType.objects.get(pk=pk)
        except ProductType.DoesNotExist:
            return Response(
                {"status": False, "message": "ProductType not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductTypeSerializer(product_type, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(updated_by=self.request.user)
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product Type created successfully.",
                },
                status=status.HTTP_200_OK,
            )

        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @superuser_required
    def patch(self, request, pk=None):
        try:
            product_type = ProductType.objects.get(pk=pk)
        except ProductType.DoesNotExist:
            return Response(
                {"status": False, "message": "ProductType not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductTypeSerializer(
            product_type, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product type partially updated successfully.",
                },
                status=status.HTTP_200_OK,
            )

        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @superuser_required
    def delete(self, request, pk=None):
        try:
            product_type = ProductType.objects.filter(pk=pk).first()
            product_type.delete()
        except ProductType.DoesNotExist:
            return Response(
                {"status": False, "message": "ProductType not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except:
            return Response(
                {
                    "status": False,
                    "message": "Cannot delete this Product type it is referenced by other objects.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"status": True, "message": "ProductType delete successfully."},
            status=status.HTTP_200_OK,
        )


class ProductAPIView(APIView):
    """
    APIView for CRUD operations on Product.
    """

    def get(self, request, pk=None, *args, **kwargs):
        product_type = self.request.data.get("product_type", None)
        if pk:
            try:
                product = Product.objects.get(pk=pk)
                serializer = ProductSerializer(product, context={"request": request})
                return Response(
                    {
                        "status": True,
                        "data": serializer.data,
                        "message": "Product arrived successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
            except Product.DoesNotExist:
                return Response(
                    {"status": False, "message": "Product not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        if request.user.is_authenticated and hasattr(request.user, "is_site_admin") and request.user.is_site_admin:
            products = Product.objects.all()
        else:
            products = Product.objects.filter(status=Product.IN_STOCK)

        if product_type:
            products = products.filter(product_type_id=product_type)

        serializer = ProductSerializer(
            products, context={"request": request}, many=True
        )
        return Response(
            {
                "status": True,
                "data": serializer.data,
                "message": "Product arrived successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @superuser_required
    def post(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(created_by=self.request.user, updated_by=self.request.user)
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product created successfully.",
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

    @superuser_required
    def put(self, request, pk=None, *args, **kwargs):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"status": False, "message": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(
            product, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(updated_by=self.request.user)
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product updated successfully.",
                },
                status=status.HTTP_200_OK,
            )

        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @superuser_required
    def patch(self, request, pk, *args, **kwargs):
        try:
            # Retrieve the product instance
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"status": False, "message": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Pass partial=True to the serializer to allow partial updates
        serializer = ProductSerializer(
            product, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product updated successfully.",
                },
                status=status.HTTP_200_OK,
            )
        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @superuser_required
    def delete(self, request, pk=None, *args, **kwargs):
        try:
            product = Product.objects.filter(pk=pk).first()
            if not product:
                return Response(
                {"status": False, "message": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
            product.delete()
            return Response(
                {"status": True, "message": "Product deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except Product.DoesNotExist:
            return Response(
                {"status": False, "message": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ProtectedError as e:
            # Extract referencing objects
            referencing_objects = [str(obj) for obj in e.protected_objects]
            return Response(
                {
                    "status": False,
                    "message": "Cannot delete this Product it is referenced by other objects.",
                    "referenced_by": referencing_objects,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class WishlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist_items = Wishlist.objects.filter(user=self.request.user)
        serializer = WishlistSerializer(wishlist_items, many=True, context={"request": request})
        return Response({"status": True, "data": serializer.data, "message": "Wishlist arrived successfully."}, status=status.HTTP_200_OK)

    def post(self, request):
        product_id = self.request.data.get("product_id")
        product = Product.objects.filter(id=product_id, status=Product.IN_STOCK).exists()
        if product:
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=self.request.user, product_id=product_id
            )

            if created:
                return Response(
                    {"status": True, "message": "Product added to wishlist."},
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {"status": False, "message": "Product already in wishlist."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"status": False, "message": "Something Went Wrong!"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request):
        product_id = self.request.query_params.get("product_id")
        wishlist_id = self.request.query_params.get("wishlist_id")

        if not product_id and not wishlist_id:
            return Response(
                {"status": False, "message": "Missing product or wishlist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if product_id:
            return self._delete_by_product_id(product_id)

        if wishlist_id:
            return self._delete_by_wishlist_id(wishlist_id)

    def _delete_by_product_id(self, product_id):
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response(
                {"status": False, "message": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        wishlist_item = Wishlist.objects.filter(product_id=product.id, user=self.request.user).first()
        if wishlist_item:
            wishlist_item.delete()
            return Response(
                {"status": True, "message": "Product removed from wishlist."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": False, "message": "Product not in wishlist."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def _delete_by_wishlist_id(self, wishlist_id):
        wishlist_item = Wishlist.objects.filter(id=wishlist_id, user=self.request.user).first()
        if wishlist_item:
            wishlist_item.delete()
            return Response(
                {"status": True, "message": "Product removed from wishlist."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": False, "message": "Wishlist item not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


class CartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the cart items for the logged-in user."""
        user_cart = ShoppingCart.objects.filter(user=self.request.user).first()
        if not user_cart:
            user_cart = ShoppingCart.objects.create(user=self.request.user)
        cart_items = CartItems.objects.filter(cart_id=user_cart.id)
        serializer = CartSerializer(cart_items, many=True)
        return Response(
            {
                "status": True,
                "data": serializer.data,
                "message": "Cart item arrived successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Add a product to the user's cart."""
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        # Validate product belongs to product_color
        productData = Product.objects.filter(
            id=product_id,
            status=Product.IN_STOCK,
        ).first()  # Get the first match, not a queryset

        if not productData:
            return Response(
                {
                    "status": False,
                    "message": "Product is out of stock.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        shoping_cart = ShoppingCart.objects.filter(user=self.request.user).first()
        if not shoping_cart:
            shoping_cart = ShoppingCart.objects.create(user=self.request.user)

        # Check if the product is already in the cart
        cart_item, created = CartItems.objects.get_or_create(
            cart=shoping_cart,
            product=productData,
            defaults={"quantity": int(quantity)},
        )

        if not created:
            # Update the quantity if the product already exists in the cart
            cart_item.quantity += int(quantity)
            cart_item.save()

        serializer = CartSerializer(cart_item)
        return Response(
            {
                "status": True,
                "data": serializer.data,
                "message": "Product added successfully.",
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request, cart_item_id):
        """Increment or decrement the quantity of a product in the cart."""
        user_cart = get_object_or_404(ShoppingCart, user=self.request.user)
        cart_item = get_object_or_404(CartItems, id=cart_item_id, cart_id=user_cart.id)
        action = request.data.get("action", None)

        if action == "increment":
            # Increase the quantity by 1
            cart_item.quantity += 1
            cart_item.save()
            serializer = CartSerializer(cart_item)
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product updated successfully.",
                },
                status=status.HTTP_200_OK,
            )

        elif action == "decrement":
            # Decrease the quantity by 1
            cart_item.quantity -= 1

            # If quantity is now 0, delete the item from the cart
            if cart_item.quantity <= 0:
                cart_item.delete()
                return Response(
                    {"status": True, "message": "Item removed from cart."},
                    status=status.HTTP_200_OK,
                )

            cart_item.save()
            serializer = CartSerializer(cart_item)
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Product updated successfully.",
                },
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"message": "Invalid action"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, cart_item_id, *args, **kwargs):
        """
        Remove an item from the user's cart.
        """
        # Get the user's cart
        try:
            user_cart = ShoppingCart.objects.filter(user=request.user).first()
        except ShoppingCart.DoesNotExist:
            return Response(
                {"status": False, "message": "Shopping cart not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Try to find the cart item within the user's cart
        try:
            cart_item = CartItems.objects.get(id=cart_item_id, cart_id=user_cart.id)
        except CartItems.DoesNotExist:
            return Response(
                {"status": False, "message": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Delete the cart item
        cart_item.delete()

        # Return success response
        return Response(
            {"status": True, "message": "Item removed from cart."},
            status=status.HTTP_200_OK,
        )


class BannerAPIView(APIView):

    def get(self, request, pk=None, *args, **kwargs):
        if pk:  # Retrieve a single banner by ID
            try:
                banner = Banner.objects.get(pk=pk)
            except Banner.DoesNotExist:
                return Response(
                    {"status": False, "message": "Banner not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = BannerSerializer(banner, context={"request": request})
            return Response(
                {
                    "status": True,
                    "message": "Banner retrieved successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        # Retrieve all banners
        banners = Banner.objects.all()
        serializer = BannerSerializer(
            banners,
            many=True,
            context={"request": request},
        )
        return Response(
            {
                "status": True,
                "message": "Banners retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @superuser_required
    def post(self, request, *args, **kwargs):
        serializer = BannerSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(created_by=self.request.user ,updated_by=self.request.user)
            return Response(
                {
                    "status": True,
                    "message": "Banner created successfully",
                    "data": serializer.data,
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

    @superuser_required
    def put(self, request, pk, *args, **kwargs):
        try:
            banner = Banner.objects.get(pk=pk)
        except Banner.DoesNotExist:
            return Response(
                {"status": False, "message": "Banner not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BannerSerializer(banner, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save(updated_by=self.request.user)
            return Response(
                {
                    "status": True,
                    "message": "Banner updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        error_message = serializers_error(serializer)
        return Response(
            {
                "status": False,
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @superuser_required
    def delete(self, request, pk, *args, **kwargs):
        try:
            banner = Banner.objects.filter(pk=pk).first()
        except Banner.DoesNotExist:
            return Response(
                {"status": False, "message": "Banner not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        banner.delete()
        return Response(
            {"status": True, "message": "Banner deleted successfully"},
            status=status.HTTP_200_OK,
        )


class ProductImageUploadView(APIView):

    @superuser_required
    def post(self, request, product_id):
        """Upload multiple images/videos for a specific ProductVariant"""
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response(
                {"status": False, "message": "No product found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        files = request.FILES.getlist('images', [])
        if not files:
            return Response({"status": False, "message": "No images/videos provided"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = []
        for file in files:
            data = {
                "product": product.id,
                "image": file
            }
            serializer = ProductImageSerializer(data=data, context={"request": request})
            if serializer.is_valid():
                serializer.save(created_by=self.request.user, updated_by=self.request.user)
                uploaded_files.append(serializer.data)
            else:
                error_message = serializers_error(serializer)
                return Response(
                    {
                        "status": False,
                        "message": error_message,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response({
            "status": True,
            "message": "Files uploaded successfully",
            "data": uploaded_files
        }, status=status.HTTP_201_CREATED)

    def get(self, request, product_id):
        """Retrieve all images/videos for a specific ProductVariant"""
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response(
                {"status": False, "message": "No product found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        images = ProductImage.objects.filter(product=product)
        serializer = ProductImageSerializer(images, many=True, context={"request": request})
        return Response({
                "status": True,
                "message": "Files arrived successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

    @superuser_required
    def delete(self, request, product_id):
        """Delete an image/video for a specific ProductVariant"""
        product_image = ProductImage.objects.filter(product_id=product_id)
        for image in product_image:
            image.image.delete(save=False)
        product_image.delete()

        return Response({"status": True, "message": "File deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ProductImageDeleteView(APIView):

    @superuser_required
    def delete(self, request, image_id):
        """Delete an image/video for a specific ProductVariant"""
        product_image = ProductImage.objects.filter(id=image_id).first()
        if not product_image:
            return Response(
                {"status": False, "message": "No product image found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Delete the file from storage
        product_image.image.delete(save=False)
        
        # Delete the database record
        product_image.delete()

        return Response(
            {"status": True, "message": "File deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )