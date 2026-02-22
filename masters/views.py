from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from masters.models import Master

@login_required
def master_dashboard(request):
    if request.user.user_type != 'master':
        return render(request, '403.html', status=403)
    try:
        master = Master.objects.get(user=request.user)
    except Master.DoesNotExist:
        return render(request, '403.html', {'error': 'Master profili topilmadi'}, status=403)
    return render(request, 'master_dashboard.html', {'master': master})