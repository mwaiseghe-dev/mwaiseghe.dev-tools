from django.db import models
from django.utils import timezone
import secrets
import hashlib
import hmac
import base64
import struct
import time
from datetime import datetime
from typing import Optional, Dict, Any
import json
import zlib
import uuid

class AdvancedLicenseKeyGenerator:
    """
    Advanced License Key Generator with multiple security layers:
    1. Cryptographic signing with HMAC
    2. Metadata embedding (client info, expiry, features)
    3. Checksum validation
    4. Anti-tampering protection
    5. Base32 encoding for human readability
    6. Version control for future compatibility
    """
    
    # Secret key for HMAC signing - In production, store this securely (environment variable)
    SECRET_KEY = "your-super-secret-key-change-this-in-production"
    VERSION = 1
    
    @classmethod
    def generate_advanced_license_key(cls, 
                                    client_id: int,
                                    client_name: str,
                                    email: str = "",
                                    expires_at: Optional[datetime] = None,
                                    max_users: int = 1,
                                    features: Dict[str, Any] = None) -> str:
        """
        Generate an advanced license key with embedded metadata and cryptographic protection.
        
        Key Structure:
        [VERSION][TIMESTAMP][CLIENT_HASH][METADATA][CHECKSUM][SIGNATURE]
        """
        if features is None:
            features = {}
            
        # 1. Create timestamp (4 bytes)
        timestamp = int(time.time())
        
        # 2. Create client hash (8 bytes) - deterministic hash of client info
        client_data = f"{client_id}:{client_name}:{email}".encode('utf-8')
        client_hash = hashlib.sha256(client_data).digest()[:8]
        
        # 3. Create metadata payload
        metadata = {
            'client_id': client_id,
            'email_hash': hashlib.md5(email.encode()).hexdigest()[:8] if email else "",
            'expires': int(expires_at.timestamp()) if expires_at else 0,
            'max_users': max_users,
            'features': features,
            'issued': timestamp
        }
        
        # Compress and encode metadata
        metadata_json = json.dumps(metadata, separators=(',', ':')).encode('utf-8')
        compressed_metadata = zlib.compress(metadata_json, level=9)
        
        # 4. Create the core payload
        core_payload = struct.pack('>BI', cls.VERSION, timestamp) + client_hash + compressed_metadata
        
        # 5. Generate checksum (CRC32 for quick validation)
        checksum = zlib.crc32(core_payload) & 0xffffffff
        
        # 6. Create HMAC signature for tamper protection
        signature = hmac.new(
            cls.SECRET_KEY.encode('utf-8'),
            core_payload + struct.pack('>I', checksum),
            hashlib.sha256
        ).digest()[:16]  # Use first 16 bytes of signature
        
        # 7. Combine all parts
        final_payload = core_payload + struct.pack('>I', checksum) + signature
        
        # 8. Encode to base32 for human readability (removes ambiguous characters)
        encoded_key = base64.b32encode(final_payload).decode('ascii').rstrip('=')
        
        # 9. Format with dashes for readability (groups of 5 characters)
        formatted_key = '-'.join([encoded_key[i:i+5] for i in range(0, len(encoded_key), 5)])
        
        return f"ALK-{formatted_key}"  # ALK = Advanced License Key
    
    @classmethod
    def validate_license_key(cls, license_key: str) -> Dict[str, Any]:
        """
        Validate and decode an advanced license key.
        Returns metadata if valid, raises exception if invalid.
        """
        try:
            # Remove prefix and dashes
            if not license_key.startswith("ALK-"):
                raise ValueError("Invalid license key format")
            
            clean_key = license_key[4:].replace('-', '')
            
            # Add padding for base32 decoding
            padding = (8 - len(clean_key) % 8) % 8
            padded_key = clean_key + '=' * padding
            
            # Decode from base32
            payload = base64.b32decode(padded_key)
            
            # Extract components
            if len(payload) < 25:  # Minimum size check
                raise ValueError("Invalid license key length")
            
            # Parse version and timestamp
            version, timestamp = struct.unpack('>BI', payload[:5])
            
            if version != cls.VERSION:
                raise ValueError(f"Unsupported license key version: {version}")
            
            # Extract client hash
            client_hash = payload[5:13]
            
            # Find where metadata ends (signature is last 16 bytes, checksum is 4 bytes before that)
            signature = payload[-16:]
            checksum = struct.unpack('>I', payload[-20:-16])[0]
            compressed_metadata = payload[13:-20]
            
            # Verify checksum
            core_payload = payload[:-20]
            expected_checksum = zlib.crc32(core_payload) & 0xffffffff
            
            if checksum != expected_checksum:
                raise ValueError("License key checksum validation failed")
            
            # Verify HMAC signature
            expected_signature = hmac.new(
                cls.SECRET_KEY.encode('utf-8'),
                core_payload + struct.pack('>I', checksum),
                hashlib.sha256
            ).digest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("License key signature validation failed")
            
            # Decompress and parse metadata
            try:
                metadata_json = zlib.decompress(compressed_metadata)
                metadata = json.loads(metadata_json.decode('utf-8'))
            except:
                raise ValueError("Failed to parse license key metadata")
            
            # Add validation status
            current_time = int(time.time())
            metadata['is_expired'] = metadata.get('expires', 0) > 0 and current_time > metadata.get('expires', 0)
            metadata['issued_datetime'] = datetime.fromtimestamp(metadata['issued'])
            metadata['expires_datetime'] = datetime.fromtimestamp(metadata['expires']) if metadata.get('expires') else None
            
            return metadata
            
        except Exception as e:
            raise ValueError(f"Invalid license key: {str(e)}")

def generate_license_key(client=None, **kwargs):
    """
    Legacy function for backward compatibility.
    Now uses the advanced generator if client object is provided.
    """
    if client and hasattr(client, 'id'):
        return AdvancedLicenseKeyGenerator.generate_advanced_license_key(
            client_id=client.id,
            client_name=client.name,
            email=getattr(client, 'email', '') or '',
            **kwargs
        )
    else:
        # Fallback to simple generation
        random_part = secrets.token_hex(8).upper()
        return f"LIC-{random_part}"

class Client(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=512, unique=True)  # Increased length for advanced keys
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='licenses')
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    max_users = models.IntegerField(default=1)
    features = models.JSONField(default=dict, blank=True)
    
    # Additional fields for advanced license management
    usage_count = models.IntegerField(default=0)  # Track usage
    last_used = models.DateTimeField(null=True, blank=True)
    hardware_fingerprint = models.CharField(max_length=255, blank=True, null=True)
    ip_restrictions = models.JSONField(default=list, blank=True)  # List of allowed IPs
    domain_restrictions = models.JSONField(default=list, blank=True)  # List of allowed domains
    
    def save(self, *args, **kwargs):
        # Generate advanced license key if not provided
        if not self.key:
            self.key = AdvancedLicenseKeyGenerator.generate_advanced_license_key(
                client_id=self.client.id,
                client_name=self.client.name,
                email=self.email or self.client.email or '',
                expires_at=self.expires_at,
                max_users=self.max_users,
                features=self.features
            )
        super().save(*args, **kwargs)
    
    def is_valid(self, ip_address=None, domain=None, hardware_fingerprint=None):
        """
        Enhanced validation with multiple security checks
        """
        # Basic active and expiry checks
        if not self.is_active:
            return False, "License is inactive"
        
        if self.expires_at and self.expires_at < timezone.now():
            return False, "License has expired"
        
        # Validate the key cryptographically
        try:
            key_metadata = AdvancedLicenseKeyGenerator.validate_license_key(self.key)
            
            # Check if key is expired based on embedded data
            if key_metadata.get('is_expired', False):
                return False, "License key has expired"
            
            # Verify client ID matches
            if key_metadata.get('client_id') != self.client.id:
                return False, "License key client mismatch"
                
        except ValueError as e:
            return False, f"Invalid license key: {str(e)}"
        
        # IP restriction check
        if ip_address and self.ip_restrictions:
            if ip_address not in self.ip_restrictions:
                return False, "IP address not authorized"
        
        # Domain restriction check
        if domain and self.domain_restrictions:
            domain_allowed = any(
                domain.endswith(allowed_domain) 
                for allowed_domain in self.domain_restrictions
            )
            if not domain_allowed:
                return False, "Domain not authorized"
        
        # Hardware fingerprint check (if configured)
        if self.hardware_fingerprint and hardware_fingerprint:
            if self.hardware_fingerprint != hardware_fingerprint:
                return False, "Hardware fingerprint mismatch"
        
        # Usage limit check
        if self.usage_count >= self.max_users:
            return False, "Maximum usage limit exceeded"
        
        return True, "License is valid"
    
    def get_key_metadata(self):
        """
        Get metadata embedded in the license key
        """
        try:
            return AdvancedLicenseKeyGenerator.validate_license_key(self.key)
        except ValueError:
            return None
    
    def increment_usage(self, ip_address=None, hardware_fingerprint=None):
        """
        Increment usage counter and update tracking info
        """
        self.usage_count += 1
        self.last_used = timezone.now()
        
        # Update hardware fingerprint if provided and not set
        if hardware_fingerprint and not self.hardware_fingerprint:
            self.hardware_fingerprint = hardware_fingerprint
        
        self.save()
    
    def reset_usage(self):
        """
        Reset usage counter (admin function)
        """
        self.usage_count = 0
        self.save()
    
    def get_remaining_uses(self):
        """
        Get remaining usage count
        """
        return max(0, self.max_users - self.usage_count)
    
    def add_ip_restriction(self, ip_address):
        """
        Add IP address to allowed list
        """
        if ip_address not in self.ip_restrictions:
            self.ip_restrictions.append(ip_address)
            self.save()
    
    def add_domain_restriction(self, domain):
        """
        Add domain to allowed list
        """
        if domain not in self.domain_restrictions:
            self.domain_restrictions.append(domain)
            self.save()
    
    def __str__(self):
        return f"{self.client.name} ({self.key[:20]}...)"
    
class LicenseManager:
    """
    Utility class for advanced license management operations
    """
    
    @staticmethod
    def generate_hardware_fingerprint(system_info: Dict[str, str]) -> str:
        """
        Generate a hardware fingerprint from system information
        """
        # Combine system information in a deterministic way
        fingerprint_data = []
        
        # Include various system identifiers
        for key in sorted(system_info.keys()):
            fingerprint_data.append(f"{key}:{system_info[key]}")
        
        combined_data = "|".join(fingerprint_data).encode('utf-8')
        return hashlib.sha256(combined_data).hexdigest()
    
    @staticmethod
    def validate_license_with_context(license_key: str, 
                                    client_id: int,
                                    ip_address: str = None,
                                    domain: str = None,
                                    hardware_fingerprint: str = None) -> Dict[str, Any]:
        """
        Comprehensive license validation with context
        """
        try:
            license_obj = License.objects.get(key=license_key, client_id=client_id)
            is_valid, message = license_obj.is_valid(
                ip_address=ip_address,
                domain=domain,
                hardware_fingerprint=hardware_fingerprint
            )
            
            return {
                'valid': is_valid,
                'message': message,
                'license': license_obj,
                'metadata': license_obj.get_key_metadata(),
                'remaining_uses': license_obj.get_remaining_uses()
            }
        except License.DoesNotExist:
            return {
                'valid': False,
                'message': 'License not found',
                'license': None,
                'metadata': None,
                'remaining_uses': 0
            }
    
    @staticmethod
    def bulk_generate_licenses(client: 'Client', 
                             count: int,
                             expires_at: Optional[datetime] = None,
                             max_users: int = 1,
                             features: Dict[str, Any] = None) -> list:
        """
        Generate multiple licenses for a client
        """
        licenses = []
        for i in range(count):
            license_obj = License(
                client=client,
                email=client.email,
                expires_at=expires_at,
                max_users=max_users,
                features=features or {}
            )
            license_obj.save()  # This will auto-generate the key
            licenses.append(license_obj)
        
        return licenses
    
    @staticmethod
    def get_license_analytics(client_id: int = None) -> Dict[str, Any]:
        """
        Get analytics for licenses
        """
        filters = {}
        if client_id:
            filters['client_id'] = client_id
        
        licenses = License.objects.filter(**filters)
        
        total_licenses = licenses.count()
        active_licenses = licenses.filter(is_active=True).count()
        expired_licenses = licenses.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        return {
            'total_licenses': total_licenses,
            'active_licenses': active_licenses,
            'expired_licenses': expired_licenses,
            'usage_stats': {
                'total_usage': sum(license.usage_count for license in licenses),
                'average_usage': licenses.aggregate(
                    avg_usage=models.Avg('usage_count')
                )['avg_usage'] or 0
            }
        }
