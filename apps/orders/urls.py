from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartView, CartItemViewSet, OrderViewSet, PromoCodeValidationView

router = DefaultRouter()
router.register(r'cart/items', CartItemViewSet, basename='cartitem')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('promo-code/validate/', PromoCodeValidationView.as_view(), name='promo-code-validate'),
    path('', include(router.urls)),
]
