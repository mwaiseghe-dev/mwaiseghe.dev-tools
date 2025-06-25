from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Client, License, LicenseManager
from .serializers import (
    ClientSerializer, LicenseSerializer, LicenseCreateSerializer,
    LicenseValidationSerializer, BulkLicenseCreateSerializer,
    LicenseUsageSerializer, LicenseAnalyticsSerializer
)

class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clients
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def licenses(self, request, pk=None):
        """
        Get all licenses for a specific client
        """
        client = self.get_object()
        licenses = client.licenses.all()
        serializer = LicenseSerializer(licenses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """
        Get analytics for a specific client
        """
        client = self.get_object()
        analytics = LicenseManager.get_license_analytics(client_id=client.id)
        return Response(analytics)

class LicenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing licenses
    """
    queryset = License.objects.all().select_related('client')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LicenseCreateSerializer
        return LicenseSerializer
    
    def get_queryset(self):
        queryset = License.objects.all().select_related('client')
        
        # Filter by client if provided
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by expiry status
        expired = self.request.query_params.get('expired')
        if expired is not None:
            if expired.lower() == 'true':
                queryset = queryset.filter(expires_at__lt=timezone.now())
            else:
                queryset = queryset.filter(
                    Q(expires_at__gte=timezone.now()) | Q(expires_at__isnull=True)
                )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a license
        """
        license_obj = self.get_object()
        license_obj.is_active = False
        license_obj.save()
        
        serializer = self.get_serializer(license_obj)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a license
        """
        license_obj = self.get_object()
        license_obj.is_active = True
        license_obj.save()
        
        serializer = self.get_serializer(license_obj)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reset_usage(self, request, pk=None):
        """
        Reset usage counter for a license
        """
        license_obj = self.get_object()
        license_obj.reset_usage()
        
        serializer = self.get_serializer(license_obj)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_ip_restriction(self, request, pk=None):
        """
        Add IP restriction to a license
        """
        license_obj = self.get_object()
        ip_address = request.data.get('ip_address')
        
        if not ip_address:
            return Response(
                {'error': 'IP address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        license_obj.add_ip_restriction(ip_address)
        serializer = self.get_serializer(license_obj)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_domain_restriction(self, request, pk=None):
        """
        Add domain restriction to a license
        """
        license_obj = self.get_object()
        domain = request.data.get('domain')
        
        if not domain:
            return Response(
                {'error': 'Domain is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        license_obj.add_domain_restriction(domain)
        serializer = self.get_serializer(license_obj)
        return Response(serializer.data)

class LicenseValidationView(APIView):
    """
    API endpoint for validating license keys
    """
    permission_classes = [permissions.AllowAny]  # This might be called by client applications
    
    def post(self, request):
        """
        Validate a license key with context
        """
        serializer = LicenseValidationSerializer(data=request.data)
        
        if serializer.is_valid():
            validation_result = serializer.validated_data['validation_result']
            
            return Response({
                'valid': validation_result['valid'],
                'message': validation_result['message'],
                'remaining_uses': validation_result['remaining_uses'],
                'metadata': validation_result['metadata']
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BulkLicenseCreateView(APIView):
    """
    API endpoint for bulk license creation
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Create multiple licenses at once
        """
        serializer = BulkLicenseCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LicenseUsageView(APIView):
    """
    API endpoint for tracking license usage
    """
    permission_classes = [permissions.AllowAny]  # This might be called by client applications
    
    def post(self, request):
        """
        Increment license usage counter
        """
        serializer = LicenseUsageSerializer(data=request.data)
        
        if serializer.is_valid():
            license_key = serializer.validated_data['license_key']
            ip_address = serializer.validated_data.get('ip_address')
            hardware_fingerprint = serializer.validated_data.get('hardware_fingerprint')
            
            try:
                license_obj = License.objects.get(key=license_key)
                
                # Validate license first
                is_valid, message = license_obj.is_valid(
                    ip_address=ip_address,
                    hardware_fingerprint=hardware_fingerprint
                )
                
                if is_valid:
                    license_obj.increment_usage(
                        ip_address=ip_address,
                        hardware_fingerprint=hardware_fingerprint
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Usage recorded successfully',
                        'remaining_uses': license_obj.get_remaining_uses()
                    })
                else:
                    return Response({
                        'success': False,
                        'message': message
                    }, status=status.HTTP_403_FORBIDDEN)
                    
            except License.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'License not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LicenseAnalyticsView(APIView):
    """
    API endpoint for license analytics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get license analytics
        """
        serializer = LicenseAnalyticsSerializer(data=request.query_params)
        
        if serializer.is_valid():
            return Response(serializer.to_representation(None))
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LicenseKeyGenerationView(APIView):
    """
    API endpoint for generating a new license key for existing license
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, license_id):
        """
        Regenerate license key for an existing license
        """
        license_obj = get_object_or_404(License, id=license_id)
        
        # Generate new key
        from .models import AdvancedLicenseKeyGenerator
        new_key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
            client_id=license_obj.client.id,
            client_name=license_obj.client.name,
            email=license_obj.email or license_obj.client.email or '',
            expires_at=license_obj.expires_at,
            max_users=license_obj.max_users,
            features=license_obj.features
        )
        
        # Update license with new key
        license_obj.key = new_key
        license_obj.save()
        
        serializer = LicenseSerializer(license_obj)
        return Response(serializer.data)
