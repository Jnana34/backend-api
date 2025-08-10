from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant, ProductReview, Wishlist


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'type', 'name', 'value', 'price_adjustment', 'stock_quantity', 'is_active']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'rating', 'title', 'comment', 'user_name', 'user_email',
                  'is_verified_purchase', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_name', 'user_email', 'is_verified_purchase', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['product'] = self.context['product']
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_wishlisted = serializers.SerializerMethodField()
    isOnSale = serializers.SerializerMethodField()
    reviewCount = serializers.IntegerField(source='review_count', read_only=True)
    price = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'original_price', 'category_name',
                  'image', 'rating', 'reviewCount', 'discount_percentage',
                  'is_in_stock', 'is_featured', 'is_wishlisted', 'isOnSale']

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        return None

    def get_is_wishlisted(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Wishlist.objects.filter(user=user, product=obj).exists()
        return False

    def get_isOnSale(self, obj):
        return bool(obj.original_price and obj.original_price > obj.price)

    def get_price(self, obj):
        return int(obj.price)

    def get_original_price(self, obj):
        return int(obj.original_price) if obj.original_price else None

    def get_rating(self, obj):
        return int(obj.rating)

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    discountPercentage = serializers.ReadOnlyField(source='discount_percentage')
    inStock = serializers.ReadOnlyField(source='is_in_stock')
    reviewCount = serializers.IntegerField(source='review_count', read_only=True)
    originalPrice = serializers.SerializerMethodField()
    isOnSale = serializers.SerializerMethodField()
    isWishlisted = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    colors = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'originalPrice', 'rating', 'reviewCount',
            'inStock', 'isWishlisted', 'isOnSale', 'discountPercentage', 'features',
            'images', 'colors', 'sizes', 'category', 'variants', 'reviews', 'created_at'
        ]
    def get_price(self, obj):
        return float(obj.price)

    def get_originalPrice(self, obj):
        return float(obj.original_price) if obj.original_price else None

    def get_isOnSale(self, obj):
        return bool(obj.original_price and obj.original_price > obj.price)

    def get_isWishlisted(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Wishlist.objects.filter(user=user, product=obj).exists()
        return False

    def get_rating(self, obj):
        return float(obj.rating)

    def get_features(self, obj):
        # If features were stored in Product.features (JSONField or text list), just return that
        return [
            "7-day battery life",
            "Water resistant up to 50m",
            "Built-in GPS",
            "Heart rate monitoring",
            "Sleep tracking",
            "100+ workout modes",
        ]  # Replace with obj.features if stored

    def get_colors(self, obj):
        colors = obj.variants.filter(type='color', is_active=True)
        return [
            {
                "id": color.value.lower().replace(" ", "-"),
                "name": color.name,
                "value": color.value,  # You could validate hex in model
                "available": color.stock_quantity > 0
            }
            for color in colors
        ]

    def get_sizes(self, obj):
        sizes = obj.variants.filter(type='size', is_active=True)
        return [
            {
                "id": size.value.lower().replace(" ", "-"),
                "name": size.name,
                "available": size.stock_quantity > 0
            }
            for size in sizes
        ]


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['id', 'created_at']


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['product']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=validated_data['user'],
            product=validated_data['product']
        )
        return wishlist_item
