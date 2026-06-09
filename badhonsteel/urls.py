"""
URL configuration for badhonsteel project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('admin-panel/transactions/', include('transactions.urls')),
    # Redirect old customer URLs to transactions app
    path('admin-panel/customers/', RedirectView.as_view(url='/admin-panel/transactions/customers/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

