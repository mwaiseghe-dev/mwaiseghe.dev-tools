from rest_framework import serializers
from .models import Client, License, LicenseManager

class ClientSerializer(serializers.ModelSerializer):
    licenses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'created_at', 'licenses_count']
        read_only_fields = ['created_at']
    
    def get_licenses_count(self, obj):
        return obj.licenses.count()

class LicenseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new licenses
    """
    class Meta:
        model = License
        fields = [
            'client', 
            'email', 
            'expires_at', 
            'max_users', 
            'features',
            'ip_restrictions', 
            'domain_restrictions'
        ]
    
    def create(self, validated_data):
        # The license key will be auto-generated in the model's save method
        return License.objects.create(**validated_data)

class LicenseSerializer(serializers.ModelSerializer):
    """
    Serializer for license display and updates
    """
    client_name = serializers.CharField(source='client.name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()
    key_metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = License
        fields = [
            'id', 'key', 'client', 'client_name', 'email', 'created_at',
            'expires_at', 'is_active', 'max_users', 'features', 'usage_count',
            'last_used', 'hardware_fingerprint', 'ip_restrictions',
            'domain_restrictions', 'is_expired', 'remaining_uses', 'key_metadata'
        ]
        read_only_fields = ['key', 'created_at', 'usage_count', 'last_used']
    
    def get_is_expired(self, obj):
        is_valid, _ = obj.is_valid()
        return not is_valid
    
    def get_remaining_uses(self, obj):
        return obj.get_remaining_uses()
    
    def get_key_metadata(self, obj):
        return obj.get_key_metadata()

class LicenseValidationSerializer(serializers.Serializer):
    """
    Serializer for license validation requests
    """
    license_key = serializers.CharField(max_length=512)
    client_id = serializers.IntegerField()
    ip_address = serializers.IPAddressField(required=False)
    domain = serializers.CharField(max_length=255, required=False)
    hardware_fingerprint = serializers.CharField(max_length=255, required=False)
    
    def validate(self, data):
        """
        Perform license validation
        """
        validation_result = LicenseManager.validate_license_with_context(
            license_key=data['license_key'],
            client_id=data['client_id'],
            ip_address=data.get('ip_address'),
            domain=data.get('domain'),
            hardware_fingerprint=data.get('hardware_fingerprint')
        )
        
        # Add validation result to the validated data
        data['validation_result'] = validation_result
        return data

class BulkLicenseCreateSerializer(serializers.Serializer):
    """
    Serializer for bulk license creation
    """
    client_id = serializers.IntegerField()
    count = serializers.IntegerField(min_value=1, max_value=100)  # Limit bulk creation
    expires_at = serializers.DateTimeField(required=False)
    max_users = serializers.IntegerField(default=1, min_value=1)
    features = serializers.JSONField(default=dict)
    
    def validate_client_id(self, value):
        try:
            Client.objects.get(id=value)
            return value
        except Client.DoesNotExist:
            raise serializers.ValidationError("Client not found")
    
    def create(self, validated_data):
        client = Client.objects.get(id=validated_data['client_id'])
        
        licenses = LicenseManager.bulk_generate_licenses(
            client=client,
            count=validated_data['count'],
            expires_at=validated_data.get('expires_at'),
            max_users=validated_data['max_users'],
            features=validated_data['features']
        )
        
        return {
            'created_count': len(licenses),
            'licenses': [LicenseSerializer(license).data for license in licenses]
        }

class LicenseUsageSerializer(serializers.Serializer):
    """
    Serializer for tracking license usage
    """
    license_key = serializers.CharField(max_length=512)
    ip_address = serializers.IPAddressField(required=False)
    hardware_fingerprint = serializers.CharField(max_length=255, required=False)
    
    def validate_license_key(self, value):
        try:
            License.objects.get(key=value)
            return value
        except License.DoesNotExist:
            raise serializers.ValidationError("License not found")

class LicenseAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for license analytics
    """
    client_id = serializers.IntegerField(required=False)
    
    def validate_client_id(self, value):
        if value:
            try:
                Client.objects.get(id=value)
                return value
            except Client.DoesNotExist:
                raise serializers.ValidationError("Client not found")
        return value
    
    def to_representation(self, instance):
        client_id = self.validated_data.get('client_id')
        return LicenseManager.get_license_analytics(client_id=client_id)
