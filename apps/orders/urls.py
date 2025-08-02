from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

urlpatterns = [
    path('createOrder/', CreateOrderView.as_view(), name='cart'),
    path('fetchOrders/', MyOrdersListView.as_view(), name='my-orders')
]
