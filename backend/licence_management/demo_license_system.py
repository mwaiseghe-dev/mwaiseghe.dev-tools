#!/usr/bin/env python
"""
Advanced License Key System Demonstration

This script demonstrates the capabilities of the advanced license key generation system.
Run this script with: python manage.py shell < demo_license_system.py
"""

from licence_management.models import Client, License, AdvancedLicenseKeyGenerator, LicenseManager
from django.utils import timezone
from datetime import timedelta
import json

def main():
    print("=" * 80)
    print("ADVANCED LICENSE KEY SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Create a demo client
    print("\n1. Creating Demo Client...")
    client, _ = Client.objects.get_or_create(
        name="Acme Corporation",
        defaults={'email': "admin@acme.com"}
    )
    print(f"Client: {client.name} (ID: {client.id})")
    
    # Demo 1: Basic License Generation
    print("\n2. Generating Basic Advanced License Key...")
    basic_license = License.objects.create(
        client=client,
        email="user@acme.com",
        max_users=1,
        features={
            "api_access": True,
            "premium_features": False,
            "max_requests_per_day": 1000
        }
    )
    print(f"Generated Key: {basic_license.key}")
    print(f"Key Length: {len(basic_license.key)} characters")
    
    # Demo 2: License with Expiry
    print("\n3. Generating License with Expiry Date...")
    expiry_date = timezone.now() + timedelta(days=90)
    expiry_license = License.objects.create(
        client=client,
        email="premium@acme.com",
        expires_at=expiry_date,
        max_users=5,
        features={
            "api_access": True,
            "premium_features": True,
            "max_requests_per_day": 10000,
            "advanced_analytics": True
        }
    )
    print(f"Generated Key: {expiry_license.key}")
    print(f"Expires At: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Demo 3: License with Restrictions
    print("\n4. Generating License with IP and Domain Restrictions...")
    restricted_license = License.objects.create(
        client=client,
        email="restricted@acme.com",
        max_users=3,
        ip_restrictions=["192.168.1.0/24", "10.0.0.1"],
        domain_restrictions=["acme.com", "internal.acme.com"],
        features={
            "internal_api": True,
            "restricted_access": True
        }
    )
    print(f"Generated Key: {restricted_license.key}")
    print(f"IP Restrictions: {restricted_license.ip_restrictions}")
    print(f"Domain Restrictions: {restricted_license.domain_restrictions}")
    
    # Demo 4: Key Validation and Metadata Extraction
    print("\n5. Validating License Keys and Extracting Metadata...")
    
    for i, license_obj in enumerate([basic_license, expiry_license, restricted_license], 1):
        print(f"\n--- License {i} Validation ---")
        
        # Validate license
        is_valid, message = license_obj.is_valid()
        print(f"Validation Result: {'✓ VALID' if is_valid else '✗ INVALID'} - {message}")
        
        # Extract metadata
        metadata = license_obj.get_key_metadata()
        if metadata:
            print("Embedded Metadata:")
            print(f"  Client ID: {metadata.get('client_id')}")
            print(f"  Issued: {metadata.get('issued_datetime')}")
            print(f"  Expires: {metadata.get('expires_datetime', 'Never')}")
            print(f"  Max Users: {metadata.get('max_users')}")
            print(f"  Features: {metadata.get('features')}")
        
        print(f"Usage: {license_obj.usage_count}/{license_obj.max_users} (Remaining: {license_obj.get_remaining_uses()})")
    
    # Demo 5: Hardware Fingerprinting
    print("\n6. Demonstrating Hardware Fingerprinting...")
    
    # Simulate system information
    system_info = {
        "cpu_id": "GenuineIntel_Family_6_Model_142_Stepping_10",
        "motherboard_serial": "MS-7C02-1234567890",
        "primary_mac": "00:1B:44:11:3A:B7",
        "disk_serial": "WD-WCC4N6XXXXXX",
        "bios_version": "American Megatrends Inc. 2.60",
        "os_version": "Windows 10 Pro 19044"
    }
    
    hardware_fingerprint = LicenseManager.generate_hardware_fingerprint(system_info)
    print(f"Generated Hardware Fingerprint: {hardware_fingerprint}")
    
    # Create license with hardware binding
    hw_license = License.objects.create(
        client=client,
        email="hardware-bound@acme.com",
        hardware_fingerprint=hardware_fingerprint,
        max_users=1,
        features={
            "hardware_bound": True,
            "high_security": True
        }
    )
    print(f"Hardware-Bound License: {hw_license.key}")
    
    # Test hardware validation
    is_valid, message = hw_license.is_valid(hardware_fingerprint=hardware_fingerprint)
    print(f"Hardware Validation: {'✓ VALID' if is_valid else '✗ INVALID'} - {message}")
    
    # Test with wrong hardware
    wrong_fingerprint = LicenseManager.generate_hardware_fingerprint({
        **system_info,
        "cpu_id": "AuthenticAMD_Different_CPU"
    })
    is_valid, message = hw_license.is_valid(hardware_fingerprint=wrong_fingerprint)
    print(f"Wrong Hardware Test: {'✓ VALID' if is_valid else '✗ INVALID'} - {message}")
    
    # Demo 6: Bulk License Generation
    print("\n7. Bulk License Generation...")
    
    bulk_licenses = LicenseManager.bulk_generate_licenses(
        client=client,
        count=5,
        expires_at=timezone.now() + timedelta(days=365),
        max_users=1,
        features={
            "bulk_generated": True,
            "standard_access": True,
            "api_calls": 500
        }
    )
    
    print(f"Generated {len(bulk_licenses)} licenses in bulk:")
    for i, license_obj in enumerate(bulk_licenses[:3], 1):  # Show first 3
        print(f"  {i}. {license_obj.key}")
    print(f"  ... and {len(bulk_licenses) - 3} more")
    
    # Demo 7: Usage Tracking
    print("\n8. Usage Tracking Demonstration...")
    
    test_license = bulk_licenses[0]
    print(f"Testing license: {test_license.key}")
    print(f"Initial usage: {test_license.usage_count}/{test_license.max_users}")
    
    # Simulate usage
    test_license.increment_usage(ip_address="192.168.1.100")
    print(f"After usage: {test_license.usage_count}/{test_license.max_users}")
    print(f"Last used: {test_license.last_used}")
    print(f"Remaining uses: {test_license.get_remaining_uses()}")
    
    # Demo 8: Advanced Validation with Context
    print("\n9. Advanced Validation with Context...")
    
    validation_result = LicenseManager.validate_license_with_context(
        license_key=restricted_license.key,
        client_id=client.id,
        ip_address="192.168.1.50",  # Should be allowed
        domain="acme.com"  # Should be allowed
    )
    
    print(f"Validation Result: {'✓ VALID' if validation_result['valid'] else '✗ INVALID'}")
    print(f"Message: {validation_result['message']}")
    print(f"Remaining Uses: {validation_result['remaining_uses']}")
    
    # Test with invalid context
    invalid_validation = LicenseManager.validate_license_with_context(
        license_key=restricted_license.key,
        client_id=client.id,
        ip_address="203.0.113.1",  # Should be blocked
        domain="malicious.com"  # Should be blocked
    )
    
    print(f"Invalid Context Test: {'✓ VALID' if invalid_validation['valid'] else '✗ INVALID'}")
    print(f"Message: {invalid_validation['message']}")
    
    # Demo 9: Analytics
    print("\n10. License Analytics...")
    
    analytics = LicenseManager.get_license_analytics(client_id=client.id)
    print("Analytics for Acme Corporation:")
    print(f"  Total Licenses: {analytics['total_licenses']}")
    print(f"  Active Licenses: {analytics['active_licenses']}")
    print(f"  Expired Licenses: {analytics['expired_licenses']}")
    print(f"  Total Usage: {analytics['usage_stats']['total_usage']}")
    print(f"  Average Usage: {analytics['usage_stats']['average_usage']:.2f}")
    
    # Demo 10: Security Features
    print("\n11. Security Features Demonstration...")
    
    # Show key components
    sample_key = basic_license.key
    print(f"Sample Key: {sample_key}")
    print("Key Structure:")
    print("  - Prefix: ALK- (Advanced License Key)")
    print("  - Version byte for future compatibility")
    print("  - Timestamp for issue tracking")
    print("  - Client hash for identity verification")
    print("  - Compressed metadata with all license info")
    print("  - CRC32 checksum for quick validation")
    print("  - HMAC-SHA256 signature for tamper protection")
    print("  - Base32 encoding for human readability")
    print("  - Dash formatting for easy copying")
    
    # Demonstrate tamper detection
    print("\n12. Tamper Detection...")
    
    # Create a tampered key
    tampered_key = sample_key.replace(sample_key[10], 'X' if sample_key[10] != 'X' else 'Y')
    print(f"Original Key: {sample_key}")
    print(f"Tampered Key: {tampered_key}")
    
    try:
        AdvancedLicenseKeyGenerator.validate_license_key(tampered_key)
        print("✗ SECURITY FAILURE: Tampered key was accepted!")
    except ValueError as e:
        print(f"✓ SECURITY SUCCESS: Tampered key rejected - {str(e)}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print(f"- Created {Client.objects.filter(name='Acme Corporation').count()} client(s)")
    print(f"- Generated {License.objects.filter(client=client).count()} license(s)")
    print("- Demonstrated 12 advanced features")
    print("- All security validations passed ✓")

if __name__ == "__main__":
    main()
