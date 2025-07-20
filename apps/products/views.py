from rest_framework import generics, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from .models import Category, Product, ProductReview, Wishlist
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductReviewSerializer, WishlistSerializer, WishlistCreateSerializer
)
from .filters import ProductFilter

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'rating', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        featured_products = self.get_queryset().filter(is_featured=True)[:8]
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get products grouped by category"""
        categories = Category.objects.filter(is_active=True).prefetch_related('products')
        data = []
        
        for category in categories:
            products = category.products.filter(is_active=True)[:4]
            data.append({
                'category': CategorySerializer(category).data,
                'products': ProductListSerializer(products, many=True, context={'request': request}).data
            })
        
        return Response(data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_wishlist(self, request, pk=None):
        """Add or remove product from wishlist"""
        product = self.get_object()
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            return Response({'message': 'Product removed from wishlist', 'wishlisted': False})
        
        return Response({'message': 'Product added to wishlist', 'wishlisted': True})
    
    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def reviews(self, request, pk=None):
        """Get or create product reviews"""
        product = self.get_object()
        
        if request.method == 'GET':
            reviews = ProductReview.objects.filter(product=product)
            serializer = ProductReviewSerializer(reviews, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Check if user already reviewed this product
            if ProductReview.objects.filter(product=product, user=request.user).exists():
                return Response(
                    {'error': 'You have already reviewed this product'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = ProductReviewSerializer(
                data=request.data,
                context={'request': request, 'product': product}
            )
            
            if serializer.is_valid():
                review = serializer.save()
                
                # Update product rating
                avg_rating = ProductReview.objects.filter(product=product).aggregate(
                    avg_rating=Avg('rating')
                )['avg_rating']
                
                product.rating = round(avg_rating, 2) if avg_rating else 0
                product.review_count = ProductReview.objects.filter(product=product).count()
                product.save()
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WishlistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WishlistCreateSerializer
        return WishlistSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if item already exists
        product = serializer.validated_data['product']
        if Wishlist.objects.filter(user=request.user, product=product).exists():
            return Response(
                {'message': 'Product already in wishlist'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        return Response(
            {'message': 'Product added to wishlist'}, 
            status=status.HTTP_201_CREATED
        )

class SearchView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if query:
            return Product.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query),
                is_active=True
            ).distinct()
        return Product.objects.none()
