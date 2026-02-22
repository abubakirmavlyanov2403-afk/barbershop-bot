from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from masters import views as masters_views

urlpatterns = [
    # ... mavjud URLlar
    path('master/dashboard/', masters_views.master_dashboard, name='master_dashboard'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('accounts/', include('allauth.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('masters/', TemplateView.as_view(template_name='masters.html'), name='masters'),
    path('services/', TemplateView.as_view(template_name='services.html'), name='services'),
    path('booking/', TemplateView.as_view(template_name='booking.html'), name='booking'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('master/dashboard/', masters_views.master_dashboard, name='master_dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)