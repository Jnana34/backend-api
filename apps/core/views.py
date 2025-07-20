from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import connection

class HealthCheckView(APIView):
    """
    Health check endpoint for the API
    """
    permission_classes = []
    
    def get(self, request):
        try:
            # Check database connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                
            health_data = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'services': {
                    'database': 'healthy',
                    'api': 'healthy'
                }
            }
            
            return Response(health_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            health_data = {
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'services': {
                    'database': 'unhealthy',
                    'api': 'healthy'
                },
                'error': str(e)
            }
            
            return Response(health_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
