# Advanced License Key Management System

A sophisticated license key generation and validation system built with Django REST Framework, featuring cryptographic security, metadata embedding, and comprehensive tracking capabilities.

## Features

### 🔐 Advanced Security
- **HMAC-SHA256 Signatures**: Cryptographic protection against tampering
- **CRC32 Checksums**: Quick integrity validation
- **Base32 Encoding**: Human-readable format without ambiguous characters
- **Version Control**: Future-proof key format versioning
- **Tamper Detection**: Immediate detection of modified keys

### 📊 Metadata Embedding
- **Client Information**: Embedded client ID and email hash
- **Expiration Dates**: Built-in expiry validation
- **Feature Flags**: License-specific feature enablement
- **Usage Limits**: Maximum user count enforcement
- **Timestamp Tracking**: Issue and expiry timestamps

### 🛡️ Access Control
- **IP Restrictions**: Limit access to specific IP addresses/ranges
- **Domain Restrictions**: Restrict usage to authorized domains
- **Hardware Fingerprinting**: Bind licenses to specific hardware
- **Usage Tracking**: Monitor and limit license usage
- **Real-time Validation**: Context-aware license validation

### 📈 Management & Analytics
- **Bulk Operations**: Generate multiple licenses efficiently
- **Usage Analytics**: Comprehensive license usage statistics
- **Admin Interface**: Full-featured Django admin integration
- **REST API**: Complete API for license management
- **Audit Trail**: Track license usage and modifications

## Key Structure

```
ALK-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-...
 │   │
 │   └── Base32-encoded payload with dashes for readability
 └── Advanced License Key prefix

Payload Structure:
[VERSION][TIMESTAMP][CLIENT_HASH][COMPRESSED_METADATA][CHECKSUM][HMAC_SIGNATURE]
```

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**:
   ```bash
   python manage.py makemigrations licence_management
   python manage.py migrate
   ```

3. **Update Settings**:
   ```python
   # In your Django settings
   INSTALLED_APPS = [
       # ... other apps
       'licence_management',
       'rest_framework',
   ]
   ```

4. **Include URLs**:
   ```python
   # In your main urls.py
   urlpatterns = [
       path('license/', include('licence_management.urls')),
   ]
   ```

## Usage Examples

### Basic License Generation

```python
from licence_management.models import Client, License

# Create a client
client = Client.objects.create(
    name="Acme Corporation",
    email="admin@acme.com"
)

# Create a license
license = License.objects.create(
    client=client,
    email="user@acme.com",
    max_users=5,
    expires_at=timezone.now() + timedelta(days=365),
    features={
        "api_access": True,
        "premium_features": True,
        "max_requests": 10000
    }
)

print(f"Generated License: {license.key}")
```

### Advanced License with Restrictions

```python
# Create license with IP and domain restrictions
restricted_license = License.objects.create(
    client=client,
    max_users=3,
    ip_restrictions=["192.168.1.0/24", "10.0.0.1"],
    domain_restrictions=["acme.com", "internal.acme.com"],
    hardware_fingerprint="sha256_hash_of_hardware_info"
)
```

### License Validation

```python
from licence_management.models import LicenseManager

# Validate license with context
result = LicenseManager.validate_license_with_context(
    license_key="ALK-XXXXX-XXXXX-...",
    client_id=1,
    ip_address="192.168.1.100",
    domain="acme.com",
    hardware_fingerprint="hardware_hash"
)

if result['valid']:
    print(f"License is valid! Remaining uses: {result['remaining_uses']}")
else:
    print(f"License validation failed: {result['message']}")
```

### Hardware Fingerprinting

```python
# Generate hardware fingerprint
system_info = {
    "cpu_id": "GenuineIntel_Family_6_Model_142",
    "motherboard_serial": "MS-7C02-1234567890",
    "primary_mac": "00:1B:44:11:3A:B7",
    "disk_serial": "WD-WCC4N6XXXXXX"
}

fingerprint = LicenseManager.generate_hardware_fingerprint(system_info)
```

### Bulk License Generation

```python
# Generate multiple licenses
licenses = LicenseManager.bulk_generate_licenses(
    client=client,
    count=10,
    expires_at=timezone.now() + timedelta(days=90),
    max_users=1,
    features={"standard_access": True}
)
```

## API Endpoints

### Clients
- `GET /license/api/clients/` - List all clients
- `POST /license/api/clients/` - Create new client
- `GET /license/api/clients/{id}/` - Get client details
- `PUT /license/api/clients/{id}/` - Update client
- `DELETE /license/api/clients/{id}/` - Delete client
- `GET /license/api/clients/{id}/licenses/` - Get client's licenses
- `GET /license/api/clients/{id}/analytics/` - Get client analytics

### Licenses
- `GET /license/api/licenses/` - List all licenses
- `POST /license/api/licenses/` - Create new license
- `GET /license/api/licenses/{id}/` - Get license details
- `PUT /license/api/licenses/{id}/` - Update license
- `DELETE /license/api/licenses/{id}/` - Delete license
- `POST /license/api/licenses/{id}/activate/` - Activate license
- `POST /license/api/licenses/{id}/deactivate/` - Deactivate license
- `POST /license/api/licenses/{id}/reset_usage/` - Reset usage counter

### Validation & Usage
- `POST /license/api/validate-license/` - Validate license key
- `POST /license/api/track-usage/` - Track license usage
- `POST /license/api/bulk-create-licenses/` - Create multiple licenses
- `GET /license/api/analytics/` - Get system analytics

## Security Considerations

### Production Deployment

1. **Secret Key Management**:
   ```python
   # Use environment variables for the HMAC secret
   SECRET_KEY = os.environ.get('LICENSE_SECRET_KEY', 'your-secret-key')
   ```

2. **Database Security**:
   - Use encrypted database connections
   - Implement proper backup strategies
   - Regular security audits

3. **API Security**:
   - Implement rate limiting
   - Use HTTPS only
   - Add API authentication
   - Monitor for suspicious activity

4. **Key Distribution**:
   - Use secure channels for key distribution
   - Implement key revocation mechanisms
   - Log all key generation and validation events

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python manage.py test licence_management

# Run specific test file
python manage.py test licence_management.test_advanced_license

# Run with coverage
coverage run --source='.' manage.py test licence_management
coverage report
```

## Demonstration

Run the interactive demonstration:

```bash
python manage.py shell < licence_management/demo_license_system.py
```

This will showcase all features of the advanced license system with real examples.

## Performance Considerations

- **Key Generation**: ~2-5ms per key (including database save)
- **Key Validation**: ~1-2ms per validation
- **Bulk Generation**: Optimized for large batches
- **Database Indexing**: Proper indexes on key and client fields
- **Caching**: Consider Redis for high-frequency validations

## Customization

### Custom Features

```python
# Extend the License model for custom features
class ExtendedLicense(License):
    custom_field = models.CharField(max_length=100)
    
    class Meta:
        proxy = True
```

### Custom Validation

```python
# Override validation logic
def custom_validation(self, **kwargs):
    # Your custom validation logic here
    is_valid, message = super().is_valid(**kwargs)
    
    # Add custom checks
    if is_valid and self.custom_field == "blocked":
        return False, "Custom validation failed"
    
    return is_valid, message
```

## Migration from Simple Keys

```python
# Migration script for existing simple license keys
from licence_management.models import License, AdvancedLicenseKeyGenerator

def migrate_simple_to_advanced():
    for license in License.objects.filter(key__startswith="LIC-"):
        # Generate new advanced key
        new_key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
            client_id=license.client.id,
            client_name=license.client.name,
            email=license.email or license.client.email or '',
            expires_at=license.expires_at,
            max_users=license.max_users,
            features=license.features
        )
        
        # Update license
        license.key = new_key
        license.save()
        print(f"Migrated license {license.id}")
```

## Support

For questions, issues, or feature requests, please refer to the project documentation or contact the development team.

## License

This license management system is proprietary software. All rights reserved.
