import logging
import sys
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async

# Modellar
from users.models import User
from masters.models import Master
from services.models import Service
from appointments.models import Appointment
from schedule.models import Schedule

# ------------------------- Logging sozlamalari -------------------------
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG qilamiz, hamma narsani ko'rish uchun
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Global bot obyekti (xabarnomalar uchun)
_bot = None

def get_bot():
    global _bot
    if _bot is None:
        from telegram import Bot
        _bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    return _bot

# ------------------------- Async DB yordamchilari -------------------------
@sync_to_async
def get_user_by_telegram_id(telegram_id):
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def create_user_from_telegram(telegram_id, first_name, last_name, username):
    # Vaqtinchalik unikal telefon raqam yaratish
    phone_digits = str(telegram_id)[-10:].zfill(10)
    temp_phone = f"+7{phone_digits}"
    
    # Username unikal bo'lishi kerak
    base_username = username or f"tg_user_{telegram_id}"
    # Unikallikni ta'minlash (agar username band bo'lsa, raqam qo'shish kerak, lekin hozircha oddiy)
    user = User.objects.create(
        username=base_username,
        first_name=first_name,
        last_name=last_name or '',
        telegram_id=telegram_id,
        user_type='client',
        phone=temp_phone
    )
    return user

@sync_to_async
def get_all_masters():
    return list(Master.objects.filter(is_available=True).select_related('user'))

@sync_to_async
def get_master_by_id(master_id):
    try:
        return Master.objects.get(id=master_id)
    except Master.DoesNotExist:
        return None

@sync_to_async
def get_services_by_master(master):
    return list(master.services.all())

@sync_to_async
def get_service_by_id(service_id):
    try:
        return Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return None

@sync_to_async
def get_available_slots(master_id, date):
    """Bo'sh vaqtlarni qaytaradi"""
    try:
        from api.utils import get_available_slots as calc_slots
        return calc_slots(master_id, date)
    except ImportError:
        logger.warning("api.utils not found, using fallback slot calculation")
        return fallback_get_available_slots(master_id, date)

def fallback_get_available_slots(master_id, date):
    try:
        schedule = Schedule.objects.get(master_id=master_id, day_of_week=date.weekday())
    except Schedule.DoesNotExist:
        return []

    busy = Appointment.objects.filter(
        master_id=master_id,
        date=date,
        status__in=['pending', 'confirmed']
    ).values_list('time', flat=True)

    slots = []
    current = datetime.combine(date, schedule.start_time)
    end = datetime.combine(date, schedule.end_time)

    while current < end:
        time_only = current.time()
        if schedule.break_start and schedule.break_end:
            if schedule.break_start <= time_only < schedule.break_end:
                current += timedelta(minutes=30)
                continue
        if time_only not in busy:
            slots.append(time_only.strftime('%H:%M'))
        current += timedelta(minutes=30)

    return slots

@sync_to_async
def create_appointment(client, master, service, date, time):
    appointment = Appointment.objects.create(
        client=client,
        master=master,
        service=service,
        date=date,
        time=time,
        status='pending'
    )
    return appointment

@sync_to_async
def get_user_appointments(user):
    return list(Appointment.objects.filter(client=user).order_by('-date', '-time')[:10])

# ------------------------- Barber (Master) uchun yordamchilar -------------------------
@sync_to_async
def get_master_appointments(master_user):
    return list(Appointment.objects.filter(
        master__user=master_user
    ).select_related('client', 'service').order_by('-date', '-time'))

@sync_to_async
def get_pending_appointments(master_user):
    return list(Appointment.objects.filter(
        master__user=master_user,
        status='pending'
    ).select_related('client', 'service').order_by('date', 'time'))

@sync_to_async
def get_master_appointments_by_date(master_user, date):
    return list(Appointment.objects.filter(
        master__user=master_user,
        date=date
    ).select_related('client', 'service').order_by('time'))

@sync_to_async
def confirm_appointment(appointment_id):
    try:
        apt = Appointment.objects.get(id=appointment_id)
        apt.status = 'confirmed'
        apt.save()
        logger.info(f"Appointment {appointment_id} confirmed")
        return True
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found for confirmation")
        return False
    except Exception as e:
        logger.error(f"Error confirming appointment {appointment_id}: {e}")
        return False

@sync_to_async
def cancel_appointment(appointment_id):
    try:
        apt = Appointment.objects.get(id=appointment_id)
        apt.status = 'cancelled'
        apt.save()
        logger.info(f"Appointment {appointment_id} cancelled")
        return True
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found for cancellation")
        return False
    except Exception as e:
        logger.error(f"Error cancelling appointment {appointment_id}: {e}")
        return False

# ------------------------- Xabarnoma funksiyalari -------------------------
async def notify_master_new_appointment(master_user, appointment):
    """Yangi bron yaratilganda masterga xabar yuborish"""
    master_telegram_id = master_user.telegram_id
    if not master_telegram_id:
        return
    text = (
        f"🆕 Новая запись!\n"
        f"Клиент: {appointment.client.first_name} {appointment.client.last_name}\n"
        f"Телефон: {appointment.client.phone}\n"
        f"Услуга: {appointment.service.name}\n"
        f"Дата: {appointment.date}\n"
        f"Время: {appointment.time.strftime('%H:%M')}\n"
        f"Статус: ожидает подтверждения"
    )
    try:
        bot = get_bot()
        await bot.send_message(chat_id=master_telegram_id, text=text)
        logger.info(f"Notification sent to master {master_telegram_id}")
    except Exception as e:
        logger.error(f"Failed to notify master {master_telegram_id}: {e}")

# ------------------------- Handlerlar -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        telegram_id = str(user.id)
        db_user = await get_user_by_telegram_id(telegram_id)

        if not db_user:
            db_user = await create_user_from_telegram(
                telegram_id=telegram_id,
                first_name=user.first_name,
                last_name=user.last_name or '',
                username=user.username
            )
            await update.message.reply_text(
                f"Добро пожаловать, {user.first_name}!\n"
                f"Вы зарегистрированы в нашем барбершопе."
            )
        else:
            await update.message.reply_text(f"С возвращением, {user.first_name}!")

        await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in start: {e}", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = await get_user_by_telegram_id(str(user_id))

    if db_user and db_user.user_type == 'master':
        keyboard = [
            [KeyboardButton("📋 Мои записи")],
            [KeyboardButton("✅ Подтвердить записи")],
            [KeyboardButton("📅 Календарь")],
            [KeyboardButton("🔙 Главное меню")]
        ]
    else:
        keyboard = [
            [KeyboardButton("📅 Записаться")],
            [KeyboardButton("👤 Мои записи")],
            [KeyboardButton("ℹ️ О нас")],
        ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    db_user = await get_user_by_telegram_id(str(user_id))

    if text == "📅 Записаться":
        await show_masters_from_text(update, context)
    elif text == "👤 Мои записи":
        await show_my_appointments_text(update, context)
    elif text == "ℹ️ О нас":
        await update.message.reply_text(
            "Наш барбершоп работает ежедневно с 9:00 до 21:00.\n"
            "Адрес: пр. Победы, 125\n"
            "Телефон: +7 (999) 123-45-67"
        )
    elif text == "📋 Мои записи" and db_user and db_user.user_type == 'master':
        await show_master_appointments(update, context)
    elif text == "✅ Подтвердить записи" and db_user and db_user.user_type == 'master':
        await show_pending_appointments(update, context)
    elif text == "📅 Календарь" and db_user and db_user.user_type == 'master':
        await show_calendar(update, context)
    elif text == "🔙 Главное меню":
        await show_main_menu(update, context)
    else:
        await update.message.reply_text("Не понял команду. Используйте меню.")

# ------------------------- Client zapis qilish -------------------------
async def show_masters_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    masters = await get_all_masters()
    if not masters:
        await update.message.reply_text("Извините, сейчас нет доступных мастеров.")
        return

    keyboard = []
    for master in masters:
        button = InlineKeyboardButton(
            f"{master.user.get_full_name()}",
            callback_data=f"master_{master.id}"
        )
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите мастера:", reply_markup=reply_markup)

async def show_my_appointments_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = await get_user_by_telegram_id(str(user_id))
    if not db_user:
        await update.message.reply_text("Ошибка: пользователь не найден.")
        return

    appointments = await get_user_appointments(db_user)
    if not appointments:
        await update.message.reply_text("У вас пока нет записей.")
        return

    text = "Ваши записи:\n\n"
    for apt in appointments[:5]:
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'completed': '✔️',
            'cancelled': '❌',
        }.get(apt.status, '❓')
        text += f"{status_emoji} {apt.date} {apt.time.strftime('%H:%M')} - {apt.service.name} ({apt.master.user.get_full_name()})\n"
    await update.message.reply_text(text)

# ------------------------- Inline button handler -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.debug(f"Callback data received: {data}")

    try:
        if data == 'book':
            await show_masters_from_callback(query, context)
        elif data.startswith('master_') and not data.startswith('master_apt_') and not data.startswith('master_confirm_') and not data.startswith('master_cancel_'):
            master_id = int(data.split('_')[1])
            context.user_data['selected_master'] = master_id
            await show_services_from_callback(query, context, master_id)
        elif data.startswith('service_'):
            service_id = int(data.split('_')[1])
            context.user_data['selected_service'] = service_id
            await ask_date_from_callback(query, context)
        elif data.startswith('date_'):
            date_str = data.split('_')[1]
            context.user_data['selected_date'] = date_str
            await show_time_slots_from_callback(query, context)
        elif data.startswith('time_'):
            time_str = data.split('_')[1]
            context.user_data['selected_time'] = time_str
            await confirm_booking_from_callback(query, context)
        elif data == 'confirm_booking':
            await create_booking_from_callback(query, context)
        elif data == 'cancel_booking':
            await query.edit_message_text("Бронирование отменено.")
            await show_main_menu_from_callback(query, context)
        # Barber uchun callbacklar
        elif data.startswith('master_apt_'):
            await master_appointment_detail_handler(update, context)
        elif data.startswith('master_confirm_'):
            await master_confirm_handler(update, context)
        elif data.startswith('master_cancel_'):
            await master_cancel_handler(update, context)
        elif data == 'master_back':
            await show_main_menu_from_callback(query, context)
        elif data.startswith('cal_day_'):
            await calendar_day_handler(update, context)
        elif data == 'back_to_days':
            await back_to_days_handler(update, context)

    except Exception as e:
        logger.error(f"Error in button_handler: {e}", exc_info=True)
        try:
            await query.edit_message_text("Произошла ошибка. Пожалуйста, начните заново.")
        except:
            pass
        await show_main_menu_from_callback(query, context)

# ------------------------- Client zapis qilish (InlineKeyboard) – yordamchi funksiyalar -------------------------
async def show_masters_from_callback(query, context):
    masters = await get_all_masters()
    if not masters:
        await query.edit_message_text("Извините, сейчас нет доступных мастеров.")
        return

    keyboard = []
    for master in masters:
        button = InlineKeyboardButton(
            f"{master.user.get_full_name()}",
            callback_data=f"master_{master.id}"
        )
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите мастера:", reply_markup=reply_markup)

async def show_services_from_callback(query, context, master_id):
    master = await get_master_by_id(master_id)
    if not master:
        await query.edit_message_text("Мастер не найден.")
        return

    services = await get_services_by_master(master)
    if not services:
        await query.edit_message_text("У этого мастера нет услуг.")
        return

    keyboard = []
    for service in services:
        button = InlineKeyboardButton(
            f"{service.name} - {service.price}₽ ({service.duration} мин)",
            callback_data=f"service_{service.id}"
        )
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите услугу:", reply_markup=reply_markup)

async def ask_date_from_callback(query, context):
    keyboard = []
    today = timezone.now().date()
    for i in range(1, 4):
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        date_display = date.strftime('%d.%m.%Y')
        keyboard.append([InlineKeyboardButton(date_display, callback_data=f'date_{date_str}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите дату:", reply_markup=reply_markup)

async def show_time_slots_from_callback(query, context):
    master_id = context.user_data.get('selected_master')
    date_str = context.user_data.get('selected_date')

    if not master_id or not date_str:
        await query.edit_message_text("Ошибка выбора. Начните заново.")
        return

    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    slots = await get_available_slots(master_id, date)

    if not slots:
        await query.edit_message_text("На эту дату нет свободного времени.")
        return

    keyboard = []
    for slot in slots:
        keyboard.append([InlineKeyboardButton(slot, callback_data=f'time_{slot}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Выберите время на {date.strftime('%d.%m.%Y')}:", reply_markup=reply_markup)

async def confirm_booking_from_callback(query, context):
    master_id = context.user_data.get('selected_master')
    service_id = context.user_data.get('selected_service')
    date_str = context.user_data.get('selected_date')
    time_str = context.user_data.get('selected_time')

    if not all([master_id, service_id, date_str, time_str]):
        await query.edit_message_text("Ошибка: не все данные выбраны. Начните заново.")
        return

    master = await get_master_by_id(master_id)
    service = await get_service_by_id(service_id)

    if not master or not service:
        await query.edit_message_text("Ошибка: мастер или услуга не найдены.")
        return

    text = (
        f"Проверьте данные:\n"
        f"Мастер: {master.user.get_full_name()}\n"
        f"Услуга: {service.name}\n"
        f"Цена: {service.price}₽\n"
        f"Дата: {date_str}\n"
        f"Время: {time_str}\n\n"
        "Подтверждаете запись?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data='confirm_booking')],
        [InlineKeyboardButton("❌ Отменить", callback_data='cancel_booking')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup)

async def create_booking_from_callback(query, context):
    try:
        user_id = query.from_user.id
        db_user = await get_user_by_telegram_id(str(user_id))
        if not db_user:
            await query.edit_message_text("Ошибка: пользователь не найден.")
            return

        master_id = context.user_data.get('selected_master')
        service_id = context.user_data.get('selected_service')
        date_str = context.user_data.get('selected_date')
        time_str = context.user_data.get('selected_time')

        if not all([master_id, service_id, date_str, time_str]):
            await query.edit_message_text("Ошибка: не все данные. Начните заново.")
            return

        master = await get_master_by_id(master_id)
        service = await get_service_by_id(service_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()

        appointment = await create_appointment(db_user, master, service, date, time)

        # Masterga xabar yuborish
        await notify_master_new_appointment(master.user, appointment)

        await query.edit_message_text(
            f"✅ Запись создана!\n"
            f"Номер записи: {appointment.id}\n"
            f"Статус: ожидание подтверждения.\n"
            f"Мы отправим уведомление, когда мастер подтвердит."
        )
        await show_main_menu_from_callback(query, context)

    except Exception as e:
        logger.error(f"Error in create_booking: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка при создании записи. Пожалуйста, попробуйте позже.")
        await show_main_menu_from_callback(query, context)

# ------------------------- Barber paneli -------------------------
async def show_master_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = await get_user_by_telegram_id(str(user_id))

    if not db_user or db_user.user_type != 'master':
        await update.message.reply_text("Эта функция только для мастеров.")
        return

    appointments = await get_master_appointments(db_user)
    if not appointments:
        await update.message.reply_text("У вас пока нет записей.")
        return

    text = "📋 Все ваши записи:\n\n"
    for apt in appointments[:10]:
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'completed': '✔️',
            'cancelled': '❌',
        }.get(apt.status, '❓')
        text += f"{status_emoji} {apt.date} {apt.time.strftime('%H:%M')} – {apt.client.first_name} {apt.client.last_name}\n"
        text += f"   Услуга: {apt.service.name}\n\n"

    await update.message.reply_text(text)

async def show_pending_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = await get_user_by_telegram_id(str(user_id))

    if not db_user or db_user.user_type != 'master':
        await update.message.reply_text("Эта функция только для мастеров.")
        return

    appointments = await get_pending_appointments(db_user)
    if not appointments:
        await update.message.reply_text("Нет неподтвержденных записей.")
        return

    keyboard = []
    for apt in appointments[:5]:
        text = f"{apt.date} {apt.time.strftime('%H:%M')} – {apt.client.first_name} {apt.client.last_name}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"master_apt_{apt.id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Неподтвержденные записи. Выберите одну:",
        reply_markup=reply_markup
    )

async def master_appointment_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        # Callback data ni logga yozish
        logger.info(f"Master detail callback: {query.data}")
        
        parts = query.data.split('_')
        if len(parts) != 3 or parts[0] != 'master' or parts[1] != 'apt':
            logger.error(f"Invalid callback data format: {query.data}")
            await query.edit_message_text("Ошибка формата данных.")
            return
        
        try:
            apt_id = int(parts[2])
        except ValueError:
            logger.error(f"apt_id is not a number: {parts[2]}")
            await query.edit_message_text("Ошибка ID записи.")
            return

        @sync_to_async
        def get_appointment_details(apt_id):
            try:
                return Appointment.objects.select_related(
                    'client', 'service', 'master__user'
                ).get(id=apt_id)
            except Appointment.DoesNotExist:
                return None
            except Exception as e:
                logger.error(f"DB error in get_appointment_details: {e}")
                return None

        apt = await get_appointment_details(apt_id)
        if not apt:
            await query.edit_message_text(f"Запись с ID {apt_id} не найдена.")
            return

        text = (
            f"📅 **Детали записи**\n\n"
            f"👤 Клиент: {apt.client.first_name} {apt.client.last_name}\n"
            f"📞 Телефон: {apt.client.phone}\n"
            f"✂️ Услуга: {apt.service.name}\n"
            f"💰 Цена: {apt.service.price}₽\n"
            f"📆 Дата: {apt.date}\n"
            f"⏰ Время: {apt.time.strftime('%H:%M')}\n"
            f"📊 Статус: {apt.get_status_display()}"
        )

        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data=f"master_confirm_{apt.id}")],
            [InlineKeyboardButton("❌ Отменить", callback_data=f"master_cancel_{apt.id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="master_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error in master_appointment_detail_handler: {e}", exc_info=True)
        await query.edit_message_text(f"Произошла ошибка: {str(e)}")

async def master_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        parts = query.data.split('_')
        if len(parts) != 3 or parts[0] != 'master' or parts[1] != 'confirm':
            logger.error(f"Invalid confirm data: {query.data}")
            await query.edit_message_text("Ошибка данных.")
            return
        apt_id = int(parts[2])
        success = await confirm_appointment(apt_id)
        if success:
            await query.edit_message_text("✅ Запись подтверждена.")
        else:
            await query.edit_message_text("❌ Ошибка при подтверждении.")
    except Exception as e:
        logger.error(f"Error in master_confirm_handler: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка.")

async def master_cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        parts = query.data.split('_')
        if len(parts) != 3 or parts[0] != 'master' or parts[1] != 'cancel':
            logger.error(f"Invalid cancel data: {query.data}")
            await query.edit_message_text("Ошибка данных.")
            return
        apt_id = int(parts[2])
        success = await cancel_appointment(apt_id)
        if success:
            await query.edit_message_text("❌ Запись отменена.")
        else:
            await query.edit_message_text("❌ Ошибка при отмене.")
    except Exception as e:
        logger.error(f"Error in master_cancel_handler: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка.")

# ------------------------- Kalendar funksiyalari (masterlar uchun) -------------------------
async def show_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = await get_user_by_telegram_id(str(user_id))
    if not db_user or db_user.user_type != 'master':
        await update.message.reply_text("Эта функция только для мастеров.")
        return

    keyboard = []
    today = timezone.now().date()
    for i in range(7):
        day = today + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        day_display = day.strftime('%d.%m.%Y')
        keyboard.append([InlineKeyboardButton(day_display, callback_data=f"cal_day_{day_str}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите день для просмотра записей:", reply_markup=reply_markup)

async def calendar_day_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        parts = query.data.split('_')
        if len(parts) != 3 or parts[0] != 'cal' or parts[1] != 'day':
            logger.error(f"Invalid calendar data: {query.data}")
            await query.edit_message_text("Ошибка данных.")
            return
        date_str = parts[2]
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        user_id = query.from_user.id
        db_user = await get_user_by_telegram_id(str(user_id))
        if not db_user or db_user.user_type != 'master':
            await query.edit_message_text("Ошибка доступа.")
            return

        appointments = await get_master_appointments_by_date(db_user, date)
        if not appointments:
            await query.edit_message_text(f"На {date.strftime('%d.%m.%Y')} записей нет.")
            return

        text = f"📅 Записи на {date.strftime('%d.%m.%Y')}:\n\n"
        keyboard = []
        for apt in appointments:
            status_emoji = {
                'pending': '⏳',
                'confirmed': '✅',
                'completed': '✔️',
                'cancelled': '❌',
            }.get(apt.status, '❓')
            text += f"{status_emoji} {apt.time.strftime('%H:%M')} – {apt.client.first_name} {apt.client.last_name} ({apt.service.name})\n"
            if apt.status == 'pending':
                keyboard.append([InlineKeyboardButton(
                    f"✅ {apt.time.strftime('%H:%M')} – {apt.client.first_name}",
                    callback_data=f"master_apt_{apt.id}"
                )])

        keyboard.append([InlineKeyboardButton("🔙 Назад к дням", callback_data="back_to_days")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in calendar_day_handler: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка.")

async def back_to_days_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        db_user = await get_user_by_telegram_id(str(user_id))
        if not db_user or db_user.user_type != 'master':
            await query.edit_message_text("Ошибка доступа.")
            return

        keyboard = []
        today = timezone.now().date()
        for i in range(7):
            day = today + timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            day_display = day.strftime('%d.%m.%Y')
            keyboard.append([InlineKeyboardButton(day_display, callback_data=f"cal_day_{day_str}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите день для просмотра записей:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in back_to_days_handler: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка.")

# ------------------------- Umumiy yordamchi -------------------------
async def show_main_menu_from_callback(query, context):
    keyboard = [
        [InlineKeyboardButton("📅 Записаться", callback_data='book')],
        [InlineKeyboardButton("👤 Мои записи", callback_data='my_appointments')],
        [InlineKeyboardButton("ℹ️ О нас", callback_data='about')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# ------------------------- Komandalar -------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start - Запустить бота\n"
        "/menu - Главное меню\n"
        "/help - Помощь"
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# ------------------------- Botni ishga tushirish -------------------------
def main():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    application.add_error_handler(error_handler)

    # Bot komandalarini o'rnatish
    async def post_init(app):
        await app.bot.set_my_commands([
            BotCommand("start", "Botni qayta ishga tushirish"),
            BotCommand("menu", "Asosiy menyu"),
            BotCommand("help", "Yordam"),
        ])
    application.post_init = post_init

    logger.info("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()