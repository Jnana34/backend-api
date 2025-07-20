import django_filters
from .models import Order

class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.ORDER_STATUS_CHOICES)
    payment_status = django_filters.ChoiceFilter(choices=Order.PAYMENT_STATUS_CHOICES)
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    total_min = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_max = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    
    class Meta:
        model = Order
        fields = ['status', 'payment_status']
