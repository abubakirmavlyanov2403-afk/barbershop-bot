from rest_framework import serializers
from users.models import User
from services.models import Category, Service
from masters.models import Master
from schedule.models import Schedule
from appointments.models import Appointment
from payments.models import Payment
from subscriptions.models import SubscriptionPlan, Subscription
from reviews.models import Review
from notifications.models import Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'phone', 'email', 'user_type', 'avatar']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'order']

class ServiceSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'duration', 'price', 'category', 'category_id', 'is_active', 'image']

class MasterSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(user_type='master'), source='user', write_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    service_ids = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='services', write_only=True, many=True)
    class Meta:
        model = Master
        fields = ['id', 'user', 'user_id', 'services', 'service_ids', 'experience', 'bio', 'rating', 'reviews_count', 'is_available']

class ScheduleSerializer(serializers.ModelSerializer):
    master = MasterSerializer(read_only=True)
    master_id = serializers.PrimaryKeyRelatedField(queryset=Master.objects.all(), source='master', write_only=True)
    class Meta:
        model = Schedule
        fields = ['id', 'master', 'master_id', 'day_of_week', 'start_time', 'end_time', 'break_start', 'break_end']

class AppointmentSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='client'), 
        source='client', 
        write_only=True
    )
    master = MasterSerializer(read_only=True)
    master_id = serializers.PrimaryKeyRelatedField(queryset=Master.objects.all(), source='master', write_only=True)
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='service', write_only=True)
    class Meta:
        model = Appointment
        fields = ['id', 'client', 'client_id', 'master', 'master_id', 'service', 'service_id', 'date', 'time', 'status', 'notes', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    appointment_id = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all(), source='appointment', write_only=True)
    class Meta:
        model = Payment
        fields = ['id', 'appointment', 'appointment_id', 'amount', 'method', 'status', 'transaction_id', 'payment_url', 'paid_at', 'created_at']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    service_ids = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='services', write_only=True, many=True)
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'services', 'service_ids', 'visits_total', 'price', 'duration_days', 'max_freeze_days', 'available_days', 'is_active']

class SubscriptionSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(user_type='client'), source='client', write_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all(), source='plan', write_only=True)
    remaining_visits = serializers.SerializerMethodField()
    class Meta:
        model = Subscription
        fields = ['id', 'client', 'client_id', 'plan', 'plan_id', 'visits_used', 'remaining_visits', 'price_paid', 'valid_from', 'valid_until', 'is_active', 'frozen_until', 'created_at']
    def get_remaining_visits(self, obj):
        return obj.remaining_visits()

class ReviewSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    appointment_id = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all(), source='appointment', write_only=True)
    class Meta:
        model = Review
        fields = ['id', 'appointment', 'appointment_id', 'rating', 'comment', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'user', 'user_id', 'type', 'title', 'message', 'is_read', 'sent_at', 'scheduled_for']