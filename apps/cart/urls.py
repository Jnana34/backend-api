from django.urls import path
from . import views

urlpatterns = [
    path("", views.CartView.as_view(), name="cart-detail"),
    path("add/", views.AddToCartView.as_view(), name="cart-add"),
    path("update/", views.UpdateCartItemView.as_view(), name="cart-item-update"),
    path("delete/", views.RemoveCartItemView.as_view(), name="cart-item-remove"),  # changed path
    path("pay/", views.CreateRazorpayOrderView.as_view(), name="razorpay-gateway"),  # changed path
]
