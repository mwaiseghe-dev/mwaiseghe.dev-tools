from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for viewsets
router = DefaultRouter()
router.register(r'clients', views.ClientViewSet)
router.register(r'licenses', views.LicenseViewSet)

urlpatterns = [
    # Router URLs
    path('api/', include(router.urls)),
    
    # Custom API endpoints
    path('api/validate-license/', views.LicenseValidationView.as_view(), name='validate-license'),
    path('api/bulk-create-licenses/', views.BulkLicenseCreateView.as_view(), name='bulk-create-licenses'),
    path('api/track-usage/', views.LicenseUsageView.as_view(), name='track-usage'),
    path('api/analytics/', views.LicenseAnalyticsView.as_view(), name='analytics'),
    path('api/licenses/<int:license_id>/regenerate-key/', views.LicenseKeyGenerationView.as_view(), name='regenerate-key'),
]
