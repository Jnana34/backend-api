from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryListView, ProductViewSet, WishlistViewSet, SearchView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('search/', SearchView.as_view(), name='product-search'),
    path('', include(router.urls)),
]
