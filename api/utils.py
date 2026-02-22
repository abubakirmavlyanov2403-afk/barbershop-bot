from datetime import datetime, timedelta, time
from appointments.models import Appointment
from schedule.models import Schedule

def get_available_slots(master_id, date):
    try:
        schedule = Schedule.objects.get(master_id=master_id, day_of_week=date.weekday())
    except Schedule.DoesNotExist:
        return []
    # Ish vaqtini 9:00-21:00 bilan cheklash (agar kerak boʻlsa)
    work_start = max(schedule.start_time, time(9,0))
    work_end = min(schedule.end_time, time(21,0))
    if work_start >= work_end:
        return []
    busy = Appointment.objects.filter(master_id=master_id, date=date, status__in=['pending','confirmed']).values_list('time', flat=True)
    slots = []
    current = datetime.combine(date, work_start)
    end = datetime.combine(date, work_end)
    while current < end:
        t = current.time()
        if schedule.break_start and schedule.break_end and schedule.break_start <= t < schedule.break_end:
            current += timedelta(minutes=30)
            continue
        if t not in busy:
            slots.append(t.strftime('%H:%M'))
        current += timedelta(minutes=30)
    return slots