from django.db import models
from django.contrib.auth import get_user_model
from apps.products.models import Product  # adjust if needed

User = get_user_model()

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart_cart')

    def __str__(self):
        return f"Cart of {self.user.email}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items_cart')
    quantity = models.PositiveIntegerField(default=1)
    is_removed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
