"""
Advanced License Key System Test Suite
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from licence_management.models import Client, License, AdvancedLicenseKeyGenerator, LicenseManager

class AdvancedLicenseKeyTest(TestCase):
    """
    Test cases for the advanced license key generation and validation system
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client.objects.create(
            name="Test Client",
            email="test@example.com"
        )
        
        self.test_features = {
            "module_a": True,
            "module_b": False,
            "api_access": True,
            "max_api_calls": 1000
        }
    
    def test_basic_license_key_generation(self):
        """Test basic license key generation"""
        license_key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
            client_id=self.client.id,
            client_name=self.client.name,
            email=self.client.email
        )
        
        # Key should start with ALK- prefix
        self.assertTrue(license_key.startswith("ALK-"))
        
        # Key should be properly formatted with dashes
        self.assertIn("-", license_key)
        
        # Key should be longer than simple keys
        self.assertGreater(len(license_key), 50)
    
    def test_license_key_validation(self):
        """Test license key validation"""
        # Generate a license key
        license_key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
            client_id=self.client.id,
            client_name=self.client.name,
            email=self.client.email,
            max_users=5,
            features=self.test_features
        )
        
        # Validate the key
        metadata = AdvancedLicenseKeyGenerator.validate_license_key(license_key)
        
        # Check metadata contents
        self.assertEqual(metadata['client_id'], self.client.id)
        self.assertEqual(metadata['max_users'], 5)
        self.assertEqual(metadata['features'], self.test_features)
        self.assertFalse(metadata['is_expired'])
    
    def test_license_key_with_expiry(self):
        """Test license key with expiration date"""
        future_date = timezone.now() + timedelta(days=30)
        
        license_key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
            client_id=self.client.id,
            client_name=self.client.name,
            email=self.client.email,
            expires_at=future_date
        )
        
        metadata = AdvancedLicenseKeyGenerator.validate_license_key(license_key)
        
        # Should not be expired
        self.assertFalse(metadata['is_expired'])
        
        # Check expiry date
        self.assertEqual(
            metadata['expires_datetime'].date(),
            future_date.date()
        )
    
    def test_license_key_tamper_protection(self):
        """Test that tampered license keys are rejected"""
        license_key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
            client_id=self.client.id,
            client_name=self.client.name,
            email=self.client.email
        )
        
        # Tamper with the key by changing a character
        tampered_key = license_key.replace(license_key[10], 'X')
        
        # Validation should fail
        with self.assertRaises(ValueError):
            AdvancedLicenseKeyGenerator.validate_license_key(tampered_key)
    
    def test_license_model_integration(self):
        """Test license model with advanced key generation"""
        expires_at = timezone.now() + timedelta(days=60)
        
        license_obj = License.objects.create(
            client=self.client,
            email=self.client.email,
            expires_at=expires_at,
            max_users=3,
            features=self.test_features
        )
        
        # Key should be automatically generated
        self.assertTrue(license_obj.key.startswith("ALK-"))
        
        # Validation should pass
        is_valid, message = license_obj.is_valid()
        self.assertTrue(is_valid)
        self.assertEqual(message, "License is valid")
        
        # Metadata should be accessible
        metadata = license_obj.get_key_metadata()
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['client_id'], self.client.id)
    
    def test_license_usage_tracking(self):
        """Test license usage tracking"""
        license_obj = License.objects.create(
            client=self.client,
            max_users=3
        )
        
        # Initial usage should be 0
        self.assertEqual(license_obj.usage_count, 0)
        self.assertEqual(license_obj.get_remaining_uses(), 3)
        
        # Increment usage
        license_obj.increment_usage(ip_address="192.168.1.1")
        
        # Check updated usage
        self.assertEqual(license_obj.usage_count, 1)
        self.assertEqual(license_obj.get_remaining_uses(), 2)
        self.assertIsNotNone(license_obj.last_used)
    
    def test_license_restrictions(self):
        """Test license IP and domain restrictions"""
        license_obj = License.objects.create(
            client=self.client,
            ip_restrictions=["192.168.1.1", "10.0.0.1"],
            domain_restrictions=["example.com", "test.org"]
        )
        
        # Valid IP should pass
        is_valid, message = license_obj.is_valid(ip_address="192.168.1.1")
        self.assertTrue(is_valid)
        
        # Invalid IP should fail
        is_valid, message = license_obj.is_valid(ip_address="192.168.1.2")
        self.assertFalse(is_valid)
        self.assertEqual(message, "IP address not authorized")
        
        # Valid domain should pass
        is_valid, message = license_obj.is_valid(domain="sub.example.com")
        self.assertTrue(is_valid)
        
        # Invalid domain should fail
        is_valid, message = license_obj.is_valid(domain="malicious.com")
        self.assertFalse(is_valid)
        self.assertEqual(message, "Domain not authorized")
    
    def test_hardware_fingerprint_generation(self):
        """Test hardware fingerprint generation"""
        system_info = {
            "cpu_id": "GenuineIntel_Family_6_Model_142_Stepping_10",
            "motherboard_serial": "ABC123DEF456",
            "mac_address": "00:11:22:33:44:55",
            "disk_serial": "WD-12345678"
        }
        
        fingerprint = LicenseManager.generate_hardware_fingerprint(system_info)
        
        # Should be a hex string
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(len(fingerprint), 64)  # SHA256 hex string
        
        # Same input should produce same fingerprint
        fingerprint2 = LicenseManager.generate_hardware_fingerprint(system_info)
        self.assertEqual(fingerprint, fingerprint2)
        
        # Different input should produce different fingerprint
        system_info2 = system_info.copy()
        system_info2["cpu_id"] = "DifferentCPU"
        fingerprint3 = LicenseManager.generate_hardware_fingerprint(system_info2)
        self.assertNotEqual(fingerprint, fingerprint3)
    
    def test_bulk_license_creation(self):
        """Test bulk license creation"""
        licenses = LicenseManager.bulk_generate_licenses(
            client=self.client,
            count=5,
            expires_at=timezone.now() + timedelta(days=30),
            max_users=2,
            features=self.test_features
        )
        
        # Should create 5 licenses
        self.assertEqual(len(licenses), 5)
        
        # All licenses should have different keys
        keys = [license.key for license in licenses]
        self.assertEqual(len(set(keys)), 5)
        
        # All licenses should have the same configuration
        for license_obj in licenses:
            self.assertEqual(license_obj.client, self.client)
            self.assertEqual(license_obj.max_users, 2)
            self.assertEqual(license_obj.features, self.test_features)
    
    def test_license_analytics(self):
        """Test license analytics"""
        # Create some test licenses
        active_license = License.objects.create(
            client=self.client,
            is_active=True,
            usage_count=5
        )
        
        expired_license = License.objects.create(
            client=self.client,
            is_active=True,
            expires_at=timezone.now() - timedelta(days=1),
            usage_count=3
        )
        
        inactive_license = License.objects.create(
            client=self.client,
            is_active=False,
            usage_count=1
        )
        
        # Get analytics
        analytics = LicenseManager.get_license_analytics(client_id=self.client.id)
        
        # Check analytics data
        self.assertEqual(analytics['total_licenses'], 3)
        self.assertEqual(analytics['active_licenses'], 2)  # Two licenses are active
        self.assertEqual(analytics['expired_licenses'], 1)  # One license is expired
        self.assertEqual(analytics['usage_stats']['total_usage'], 9)  # 5 + 3 + 1
    
    def test_license_validation_with_context(self):
        """Test comprehensive license validation with context"""
        license_obj = License.objects.create(
            client=self.client,
            max_users=1,
            ip_restrictions=["192.168.1.1"]
        )
        
        # Test validation with valid context
        result = LicenseManager.validate_license_with_context(
            license_key=license_obj.key,
            client_id=self.client.id,
            ip_address="192.168.1.1"
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['message'], "License is valid")
        self.assertIsNotNone(result['metadata'])
        
        # Test validation with invalid IP
        result = LicenseManager.validate_license_with_context(
            license_key=license_obj.key,
            client_id=self.client.id,
            ip_address="192.168.1.2"
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['message'], "IP address not authorized")
    
    def test_license_key_uniqueness(self):
        """Test that generated license keys are unique"""
        keys = set()
        
        # Generate 100 keys
        for i in range(100):
            key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
                client_id=self.client.id,
                client_name=self.client.name,
                email=f"test{i}@example.com"
            )
            keys.add(key)
        
        # All keys should be unique
        self.assertEqual(len(keys), 100)

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
