from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from apps.products.models import Product
from .serializers import CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer
from django.shortcuts import get_object_or_404
from rest_framework.parsers import JSONParser
import razorpay

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(f"[DEBUG] User {request.user} requested cart details")
        cart, created = Cart.objects.get_or_create(user=request.user)
        if created:
            print(f"[DEBUG] Created new cart for user {request.user}")
        # ✅ Only fetch non-deleted items
        items = CartItem.objects.filter(cart=cart, is_removed=False)
        print(f"[DEBUG] Cart {cart.id} has {items.count()} items")
        serializer = CartItemSerializer(items, many=True)
        print(f"[DEBUG] Serialized cart items: {serializer.data}")
        return Response(serializer.data)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(f"[DEBUG] Raw request data: {request.data}")

        # Support both flat and nested formats
        if isinstance(request.data.get("product_id"), dict):
            nested_data = request.data.get("product_id", {})
            product_id = nested_data.get("id")
            quantity = nested_data.get("quantity", 1)
        else:
            product_id = request.data.get("product_id")
            quantity = request.data.get("quantity", 1)

        if not product_id:
            return Response(
                {"detail": "Product ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            item = CartItem.objects.get(cart=cart, product=product)
            if item.is_removed:
                # Reactivate item if it was removed earlier
                item.is_removed = False
                item.quantity = 1
                item.save()
                return Response({"detail": "Item restored in cart"}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Item already in cart"}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            # Create new item
            item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)
            return Response({"detail": "Item added to cart"}, status=status.HTTP_200_OK)




class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        print(f"[DEBUG] Raw request data: {request.data}")

        data = request.data.get("data", {})
        print(f"[DEBUG] Extracted data: {data}")

        serializer = UpdateCartItemSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        print(f"[DEBUG] UpdateCartItemSerializer validated data: {serializer.validated_data}")

        cart = get_object_or_404(Cart, user=request.user)
        print(f"[DEBUG] User's cart found: {cart.id}")

        product_id = serializer.validated_data["product_id"]
        item = get_object_or_404(CartItem, product_id=product_id, cart=cart)
        print(f"[DEBUG] CartItem found: {item.id} with current quantity {item.quantity}")

        item.quantity = serializer.validated_data["quantity"]
        print(f"[DEBUG] Updating quantity to {item.quantity}")
        item.save()
        print("[DEBUG] CartItem updated successfully")

        return Response({"detail": "Cart item updated"}, status=status.HTTP_200_OK)



class RemoveCartItemView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def delete(self, request):
        product_id = request.data.get("productId")
        print(f"[DEBUG] User {request.user} wants to remove product {product_id} from cart")

        if not product_id:
            return Response({"error": "Missing productId in request"}, status=status.HTTP_400_BAD_REQUEST)

        cart = get_object_or_404(Cart, user=request.user)
        print(f"[DEBUG] Found cart {cart.id} for user {request.user}")

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id, is_removed=False)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)

        item.is_removed = True
        item.save()

        print(f"[DEBUG] Marked CartItem {item.id} as removed (is_removed=True)")
        return Response({"detail": "Item marked as removed"}, status=status.HTTP_204_NO_CONTENT)
    
class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("[DEBUG] Raw request data:", request.data)

        # Handle nested payload
        amount_data = request.data.get("data", {}).get("amount", {})
        amount = amount_data.get("amount")

        if amount is None:
            return Response({"error": "Amount not provided"}, status=400)

        try:
            client = razorpay.Client(auth=("rzp_test_iyBzWTE9HK1xVS","3erTsDLgwmfbWwrNBORrY22F"))
            print("authenticated")
            order = client.order.create({
                "amount": int(float(amount) * 100),  # convert to paise
                "currency": "INR",
                "payment_capture": 1
            })

            return Response(order)

        except Exception as e:
            print("[ERROR] Razorpay order creation failed:", str(e))
            return Response({"error": "Payment initiation failed"}, status=500)
class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        print(f"[DEBUG] User {request.user} requested to clear their cart")

        # Get or create user's cart
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Soft-delete all items (if you want to keep history) 
        updated_count = CartItem.objects.filter(cart=cart, is_removed=False).update(is_removed=True)

        print(f"[DEBUG] Cleared {updated_count} items from cart {cart.id}")

        return Response(
            {"detail": f"Cleared {updated_count} items from cart"},
            status=status.HTTP_200_OK,
        )
