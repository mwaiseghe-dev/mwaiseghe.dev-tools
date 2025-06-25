from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import Client, License

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'licenses_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at']
    
    def licenses_count(self, obj):
        count = obj.licenses.count()
        if count > 0:
            url = reverse('admin:licence_management_license_changelist') + f'?client__id__exact={obj.id}'
            return format_html('<a href="{}">{} licenses</a>', url, count)
        return '0 licenses'
    licenses_count.short_description = 'Licenses'

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = [
        'truncated_key', 'client', 'is_active', 'is_expired_status', 
        'usage_info', 'created_at', 'expires_at'
    ]
    list_filter = [
        'is_active', 'created_at', 'expires_at', 'client'
    ]
    search_fields = ['key', 'client__name', 'email']
    readonly_fields = [
        'key', 'created_at', 'key_metadata_display', 'validation_status'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'client', 'email', 'created_at')
        }),
        ('License Configuration', {
            'fields': ('expires_at', 'is_active', 'max_users', 'features')
        }),
        ('Usage Tracking', {
            'fields': ('usage_count', 'last_used', 'hardware_fingerprint')
        }),
        ('Restrictions', {
            'fields': ('ip_restrictions', 'domain_restrictions'),
            'classes': ('collapse',)
        }),
        ('Advanced', {
            'fields': ('key_metadata_display', 'validation_status'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_licenses', 'deactivate_licenses', 'reset_usage_counters']
    
    def truncated_key(self, obj):
        if len(obj.key) > 30:
            return f"{obj.key[:30]}..."
        return obj.key
    truncated_key.short_description = 'License Key'
    
    def is_expired_status(self, obj):
        is_valid, message = obj.is_valid()
        if is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ {}</span>', message)
    is_expired_status.short_description = 'Status'
    
    def usage_info(self, obj):
        remaining = obj.get_remaining_uses()
        if remaining > 0:
            color = 'green' if remaining > obj.max_users * 0.5 else 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{}/{} (remaining: {})</span>',
            color, obj.usage_count, obj.max_users, remaining
        )
    usage_info.short_description = 'Usage'
    
    def key_metadata_display(self, obj):
        metadata = obj.get_key_metadata()
        if metadata:
            formatted_json = json.dumps(metadata, indent=2, default=str)
            return format_html('<pre>{}</pre>', formatted_json)
        return 'No metadata available'
    key_metadata_display.short_description = 'Key Metadata'
    
    def validation_status(self, obj):
        try:
            is_valid, message = obj.is_valid()
            if is_valid:
                return format_html('<span style="color: green;">✓ {}</span>', message)
            else:
                return format_html('<span style="color: red;">✗ {}</span>', message)
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    validation_status.short_description = 'Validation Status'
    
    def activate_licenses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} licenses were activated.')
    activate_licenses.short_description = 'Activate selected licenses'
    
    def deactivate_licenses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} licenses were deactivated.')
    deactivate_licenses.short_description = 'Deactivate selected licenses'
    
    def reset_usage_counters(self, request, queryset):
        for license_obj in queryset:
            license_obj.reset_usage()
        self.message_user(request, f'{queryset.count()} license usage counters were reset.')
    reset_usage_counters.short_description = 'Reset usage counters'
