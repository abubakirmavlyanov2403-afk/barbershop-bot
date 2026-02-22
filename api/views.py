from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
from .serializers import *
from .utils import get_available_slots
from users.models import User
from services.models import Category, Service
from masters.models import Master
from schedule.models import Schedule
from appointments.models import Appointment
from payments.models import Payment
from subscriptions.models import SubscriptionPlan, Subscription
from reviews.models import Review
from notifications.models import Notification
from django.contrib.auth.hashers import make_password
import random
import string

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    @action(detail=False, methods=['get'], url_path='me')
    def get_current_user(self, request):
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        return Response({'error':'Not authenticated'}, status=401)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_id>\d+)')
    def by_category(self, request, category_id=None):
        services = self.queryset.filter(category_id=category_id)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)

class MasterViewSet(viewsets.ModelViewSet):
    queryset = Master.objects.filter(is_available=True)
    serializer_class = MasterSerializer
    @action(detail=True, methods=['get'], url_path='schedule')
    def get_schedule(self, request, pk=None):
        master = self.get_object()
        schedule = Schedule.objects.filter(master=master)
        serializer = ScheduleSerializer(schedule, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['get'], url_path='reviews')
    def get_reviews(self, request, pk=None):
        master = self.get_object()
        appointments = Appointment.objects.filter(master=master, status='completed')
        reviews = Review.objects.filter(appointment__in=appointments)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Sana bo‘yicha filter
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Usta bo‘yicha filter
        master_id = self.request.query_params.get('master')
        if master_id:
            queryset = queryset.filter(master_id=master_id)
        
        # Mijoz bo‘yicha filter
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # STATUS BO‘YICHA FILTER (yangi qator)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_appointment(self, request, pk=None):
        apt = self.get_object()
        apt.status = 'confirmed'
        apt.save()
        return Response({'status':'confirmed'})
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_appointment(self, request, pk=None):
        apt = self.get_object()
        apt.status = 'cancelled'
        apt.save()
        return Response({'status':'cancelled'})
    def create(self, request, *args, **kwargs):
        try:
            client_name = request.data.get('client_name')
            client_phone = request.data.get('client_phone')
            
            # Agar mijoz ma'lumotlari berilgan bo'lsa
            if client_phone and client_name:
                # Telefon raqam formatini tekshirish
                if not client_phone.startswith('+7') or len(client_phone) != 12:
                    return Response(
                        {'error': 'Телефон должен быть в формате +7XXXXXXXXXX'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Mijozni telefon raqam orqali topish
                try:
                    client = User.objects.get(phone=client_phone)
                except User.DoesNotExist:
                    # Yangi mijoz yaratish
                    # Ism va familiyani ajratish
                    name_parts = client_name.strip().split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    # Unikal username yaratish (telefon raqamdan)
                    base_username = f"client_{client_phone[1:]}"
                    username = base_username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1
                    
                    # Yangi mijoz yaratish
                    client = User.objects.create(
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        phone=client_phone,
                        user_type='client'
                    )
                    print(f"Yangi mijoz yaratildi: ID={client.id}, phone={client_phone}")
                
                # client mavjudligini tekshirish
                if client and client.id:
                    # client_id ni so'rovga qo'shish
                    request.data['client_id'] = client.id
                else:
                    return Response(
                        {'error': 'Не удалось создать или найти клиента'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Asosiy create metodini chaqirish
            return super().create(request, *args, **kwargs)
    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Server xatoligi: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.filter(is_active=True)
    serializer_class = SubscriptionSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client')
        if client_id: queryset = queryset.filter(client_id=client_id)
        return queryset

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_as_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'status':'marked as read'})

class AvailableSlotsView(APIView):
    def get(self, request):
        master_id = request.query_params.get('master_id')
        date_str = request.query_params.get('date')
        if not master_id or not date_str:
            return Response({'error':'master_id and date required'}, status=400)
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error':'Invalid date format'}, status=400)
        slots = get_available_slots(master_id, date)
        return Response({'master_id':master_id, 'date':date_str, 'available_slots':slots})