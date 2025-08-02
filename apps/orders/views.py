from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import OrderCreateRawSerializer,SimpleOrderListSerializer
from .models import Order

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateRawSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response({
            "order_id": str(order.id),
            "order_number": order.order_number,
            "message": "Order created."
        }, status=status.HTTP_201_CREATED)
class MyOrdersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = SimpleOrderListSerializer(orders, many=True)
        return Response(serializer.data)