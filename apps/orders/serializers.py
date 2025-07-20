from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, PromoCode
from apps.products.serializers import ProductListSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'subtotal']
        read_only_fields = ['id', 'subtotal']

class CartItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['product', 'quantity']
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value
    
    def create(self, validated_data):
        cart = self.context['cart']
        product = validated_data['product']
        quantity = validated_data['quantity']
        
        # Check stock
        if product.stock_quantity < quantity:
            raise serializers.ValidationError(f"Only {product.stock_quantity} items available in stock.")
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            if product.stock_quantity < cart_item.quantity:
                raise serializers.ValidationError(f"Only {product.stock_quantity} items available in stock.")
            cart_item.save()
        
        return cart_item

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'updated_at']
        read_only_fields = ['id', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_price', 'quantity', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status',
            'subtotal', 'tax_amount', 'shipping_amount', 'discount_amount', 'total_amount',
            'shipping_name', 'shipping_phone', 'shipping_address',
            'payment_method', 'tracking_number',
            'created_at', 'updated_at', 'shipped_at', 'delivered_at',
            'items'
        ]
        read_only_fields = [
            'id', 'order_number', 'created_at', 'updated_at', 'shipped_at', 'delivered_at'
        ]

class OrderCreateSerializer(serializers.ModelSerializer):
    shipping_address_id = serializers.UUIDField(write_only=True, required=False)
    payment_method_id = serializers.UUIDField(write_only=True, required=False)
    promo_code = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Order
        fields = [
            'shipping_name', 'shipping_phone', 'shipping_address',
            'billing_name', 'billing_phone', 'billing_address',
            'payment_method', 'shipping_address_id', 'payment_method_id', 'promo_code'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Get user's cart
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Cart is empty.")
        
        if not cart.items.exists():
            raise serializers.ValidationError("Cart is empty.")
        
        # Calculate totals
        subtotal = cart.total_price
        tax_rate = 0.1  # 10% tax
        tax_amount = subtotal * tax_rate
        shipping_amount = 10.00 if subtotal < 50 else 0  # Free shipping over $50
        discount_amount = 0
        
        # Apply promo code if provided
        promo_code = validated_data.pop('promo_code', None)
        if promo_code:
            try:
                promo = PromoCode.objects.get(code=promo_code)
                if promo.is_valid() and subtotal >= promo.minimum_amount:
                    if promo.discount_type == 'percentage':
                        discount_amount = subtotal * (promo.discount_value / 100)
                    else:
                        discount_amount = promo.discount_value
                    
                    promo.usage_count += 1
                    promo.save()
            except PromoCode.DoesNotExist:
                raise serializers.ValidationError("Invalid promo code.")
        
        total_amount = subtotal + tax_amount + shipping_amount - discount_amount
        
        # Remove write-only fields
        validated_data.pop('shipping_address_id', None)
        validated_data.pop('payment_method_id', None)
        
        # Create order
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            **validated_data
        )
        
        # Create order items from cart
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity,
                subtotal=cart_item.subtotal
            )
            
            # Update product stock
            product = cart_item.product
            product.stock_quantity -= cart_item.quantity
            product.save()
        
        # Clear cart
        cart.items.all().delete()
        
        return order

class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ['code', 'discount_type', 'discount_value', 'minimum_amount']

class PromoCodeValidationSerializer(serializers.Serializer):
    code = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
