from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import Product  # ensure it's the correct path

class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price"]  # Add more fields as needed


# class CartItemSerializer(serializers.ModelSerializer):
#     product = ProductMiniSerializer(read_only=True)

#     class Meta:
#         model = CartItem
#         fields = ["id", "product", "quantity"]

# serializers.py

from rest_framework import serializers
from .models import CartItem
from apps.products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name')
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2)
    originalPrice = serializers.DecimalField(source='product.original_price', max_digits=10, decimal_places=2, required=False)
    image = serializers.SerializerMethodField()
    quantity = serializers.IntegerField()
    inStock = serializers.SerializerMethodField()
    color = serializers.CharField(source='product.color')
    product_id = serializers.CharField()

    class Meta:
        model = CartItem
        fields = ['product_id', 'name', 'price', 'originalPrice', 'image', 'quantity', 'color','inStock']

    def get_image(self, obj):
        # You may update this if your product has an image field in another model or plan to support images later.
        return "/placeholder.svg"

    def get_inStock(self, obj):
        return obj.product.stock_quantity > 0



class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()  # ⬅️ changed from IntegerField to UUIDField
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
