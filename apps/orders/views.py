from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Order, PromoCode
from .serializers import (
    CartSerializer, CartItemSerializer, CartItemCreateSerializer,
    OrderSerializer, OrderCreateSerializer, PromoCodeValidationSerializer
)
from .filters import OrderFilter

class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CartItemCreateSerializer
        return CartItemSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'create':
            cart, created = Cart.objects.get_or_create(user=self.request.user)
            context['cart'] = cart
        return context
    
    def update(self, request, *args, **kwargs):
        """Update cart item quantity"""
        cart_item = self.get_object()
        quantity = request.data.get('quantity', cart_item.quantity)
        
        if quantity < 1:
            return Response({'error': 'Quantity must be at least 1'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check stock
        if cart_item.product.stock_quantity < quantity:
            return Response({
                'error': f'Only {cart_item.product.stock_quantity} items available in stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared successfully'})

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        
        if order.status not in ['pending', 'confirmed']:
            return Response(
                {'error': 'Order cannot be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        # Restore product stock
        for item in order.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save()
        
        return Response({'message': 'Order cancelled successfully'})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get order summary statistics"""
        orders = self.get_queryset()
        
        summary = {
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status='pending').count(),
            'delivered_orders': orders.filter(status='delivered').count(),
            'cancelled_orders': orders.filter(status='cancelled').count(),
            'total_spent': sum(order.total_amount for order in orders if order.payment_status == 'paid'),
        }
        
        return Response(summary)

class PromoCodeValidationView(generics.GenericAPIView):
    serializer_class = PromoCodeValidationSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        total_amount = serializer.validated_data['total_amount']
        
        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response({'error': 'Invalid promo code'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not promo.is_valid():
            return Response({'error': 'Promo code is expired or inactive'}, status=status.HTTP_400_BAD_REQUEST)
        
        if total_amount < promo.minimum_amount:
            return Response({
                'error': f'Minimum order amount of ${promo.minimum_amount} required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate discount
        if promo.discount_type == 'percentage':
            discount_amount = total_amount * (promo.discount_value / 100)
        else:
            discount_amount = promo.discount_value
        
        return Response({
            'valid': True,
            'discount_amount': discount_amount,
            'discount_type': promo.discount_type,
            'discount_value': promo.discount_value
        })
