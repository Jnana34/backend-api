from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem
from apps.cart.models import Cart, CartItem  # <-- correct import

class OrderCreateRawSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'shipping_name', 'shipping_phone', 'shipping_address',
            'billing_name', 'billing_phone', 'billing_address',
            'payment_method'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        cart = Cart.objects.get(user=user)
        cart_items = cart.items.select_related('product')

        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        tax = subtotal * Decimal("0.10")
        shipping = Decimal("10.00") if subtotal < Decimal("50.00") else Decimal("0.00")
        discount = Decimal("0.00")
        total = subtotal + tax + shipping - discount

        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax_amount=tax,
            shipping_amount=shipping,
            discount_amount=discount,
            total_amount=total,
            **validated_data
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
                subtotal=item.product.price * item.quantity
            )

        cart.items.all().delete()
        return order

class SimpleOrderListSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='order_number')
    date = serializers.SerializerMethodField()
    total = serializers.DecimalField(source='total_amount', max_digits=10, decimal_places=2)
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'date', 'total', 'status', 'items']

    def get_date(self, obj):
        # Format datetime to date string 'YYYY-MM-DD'
        return obj.created_at.strftime('%Y-%m-%d')

    def get_items(self, obj):
        return obj.items.count()