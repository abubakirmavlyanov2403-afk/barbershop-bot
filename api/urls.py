from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'services', views.ServiceViewSet)
router.register(r'masters', views.MasterViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'appointments', views.AppointmentViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'subscription-plans', views.SubscriptionPlanViewSet)
router.register(r'subscriptions', views.SubscriptionViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'notifications', views.NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('available-slots/', views.AvailableSlotsView.as_view(), name='available-slots'),
    path('api-auth/', include('rest_framework.urls')),
]