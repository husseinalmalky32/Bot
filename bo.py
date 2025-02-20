import os
from dotenv import load_dotenv
import telebot
from telebot import types
import time
import json
import logging

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot_log.log'
)
logger = logging.getLogger(__name__)

# تحميل المتغيرات البيئية
load_dotenv()

# تهيئة البوت
BOT_TOKEN = os.getenv('BOT_TOKEN', '7748208067:AAEJ3urMl0dPS9Y3jVEkoIXsw8dKeshaXds')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7452139728'))
bot = telebot.TeleBot(BOT_TOKEN)

class DataManager:
    def __init__(self):
        self.data = {
            'practical': {str(i): {'polls': [], 'audio': None} for i in range(1, 7)},
            'theoretical': {str(i): {'polls': [], 'audio': None} for i in range(1, 12)}
        }
        self.stats = {
            'total_polls': 0,
            'total_audio': 0,
            'practical_polls': 0,
            'theoretical_polls': 0,
            'last_update': ''
        }
        self.load_data()

    def save_data(self):
        try:
            with open('bot_data.json', 'w', encoding='utf-8') as f:
                json.dump({'data': self.data, 'stats': self.stats}, f, ensure_ascii=False, indent=2)
            logger.info("Data saved successfully")
            return True
        except Exception as e:
            logger.error(f"Save data error: {e}")
            return False

    def load_data(self):
        try:
            with open('bot_data.json', 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                self.data = saved_data.get('data', self.data)
                self.stats = saved_data.get('stats', self.stats)
            logger.info("Data loaded successfully")
            return True
        except FileNotFoundError:
            logger.info("No data file found, creating new one")
            return self.save_data()
        except Exception as e:
            logger.error(f"Load data error: {e}")
            return False

    def add_content(self, section, number, content_type, content_data):
        try:
            if section in self.data and number in self.data[section]:
                if content_type == 'poll':
                    if not all(key in content_data for key in ['question', 'options']):
                        logger.error("Invalid poll data")
                        return False
                    self.data[section][number]['polls'].append(content_data)
                    self.stats['total_polls'] += 1
                    self.stats[f'{section}_polls'] += 1
                elif content_type == 'audio':
                    if 'file_id' not in content_data:
                        logger.error("Invalid audio data")
                        return False
                    self.data[section][number]['audio'] = content_data
                    self.stats['total_audio'] += 1
                
                self.stats['last_update'] = time.strftime("%Y-%m-%d %H:%M:%S")
                return self.save_data()
            return False
        except Exception as e:
            logger.error(f"Add content error: {e}")
            return False

    def get_content(self, section, number, content_type):
        try:
            if section in self.data and number in self.data[section]:
                return self.data[section][number][content_type]
            return None
        except Exception as e:
            logger.error(f"Get content error: {e}")
            return None

class UserState:
    def __init__(self):
        self.states = {}

    def set_state(self, user_id, state, **kwargs):
        try:
            user_id = str(user_id)
            current_state = self.states.get(user_id, {})
            current_state.update({'state': state, **kwargs})
            self.states[user_id] = current_state
            logger.info(f"State set for user {user_id}: {state}")
            return True
        except Exception as e:
            logger.error(f"Set state error: {e}")
            return False

    def get_state(self, user_id):
        try:
            user_id = str(user_id)
            return self.states.get(user_id, {})
        except Exception as e:
            logger.error(f"Get state error: {e}")
            return {}

    def clear_state(self, user_id, keep_admin=True):
        try:
            user_id = str(user_id)
            if user_id in self.states:
                if keep_admin:
                    admin_mode = self.states[user_id].get('admin_mode', True)
                    self.states[user_id] = {'admin_mode': admin_mode}
                else:
                    self.states[user_id] = {}
            logger.info(f"State cleared for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Clear state error: {e}")
            return False

# تهيئة لوحات المفاتيح
def create_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add('نظم نظري', 'نظم عملي')
    return keyboard

def create_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add('إضافة شرح صوتي', 'إضافة اختبار')
    keyboard.add('وضع المستخدم')
    keyboard.add('العودة للقائمة الرئيسية')
    return keyboard

def create_section_keyboard(section):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    max_lectures = 11 if section == 'theoretical' else 6
    buttons = [f"محاضرة {i}" for i in range(1, max_lectures + 1)]
    keyboard.add(*buttons)
    keyboard.row('العودة للقائمة الرئيسية')
    return keyboard

def create_lecture_keyboard(section, number):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(f"اختبار المحاضرة {number}")
    keyboard.row('العودة للقائمة الرئيسية')
    return keyboard

yes_no_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
yes_no_keyboard.add('نعم', 'لا')

# تهيئة المدراء
data_manager = DataManager()
user_states = UserState()

logger.info("Bot configuration loaded successfully")
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        if user_id == ADMIN_ID:
            user_states.set_state(user_id, 'admin_menu', admin_mode=True)
            bot.send_message(
                message.chat.id,
                f"مرحباً {user_name}! 👋\n\nأنت في وضع المدير",
                reply_markup=create_admin_keyboard()
            )
        else:
            user_states.set_state(user_id, 'main_menu', admin_mode=False)
            bot.send_message(
                message.chat.id,
                f"مرحباً {user_name}! 👋\n\nمرحباً بك في بوت نظم المعلومات",
                reply_markup=create_main_keyboard()
            )
        logger.info(f"User {user_id} started the bot")
    except Exception as e:
        logger.error(f"Start command error: {e}")
        bot.send_message(message.chat.id, "حدث خطأ، الرجاء المحاولة مرة أخرى /start")

def show_lecture_content(message, section, number):
    """عرض محتوى المحاضرة"""
    try:
        # إرسال الشرح الصوتي إذا وجد
        audio = data_manager.get_content(section, number, 'audio')
        if audio:
            try:
                caption = f"🎤 الشرح الصوتي للمحاضرة {number}"

                # إرسال الشرح الصوتي
                if audio['type'] == 'voice':
                    bot.send_voice(
                        message.chat.id,
                        audio['file_id'],
                        caption=caption
                    )
                else:
                    bot.send_audio(
                        message.chat.id,
                        audio['file_id'],
                        caption=caption
                    )
                
                # إرسال رسالة منفصلة مع زر الاختبار
                keyboard = create_lecture_keyboard(section, number)
                bot.send_message(
                    message.chat.id,
                    f"📝 للاختبار اضغط على 'اختبار المحاضرة {number}'",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error sending audio: {e}")
                bot.send_message(
                    message.chat.id,
                    "❌ عذراً، حدث خطأ في تحميل الشرح الصوتي",
                    reply_markup=create_lecture_keyboard(section, number)
                )
        else:
            keyboard = create_lecture_keyboard(section, number)
            bot.send_message(
                message.chat.id,
                f"⚠️ لا يوجد شرح صوتي للمحاضرة {number}\n\nيمكنك مشاهدة الاختبار بالضغط على 'اختبار المحاضرة {number}'",
                reply_markup=keyboard
            )

        # حفظ معلومات المحاضرة في حالة المستخدم
        user_states.set_state(
            message.from_user.id,
            'viewing_lecture',
            section=section,
            number=number
        )

    except Exception as e:
        logger.error(f"Show lecture content error: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في عرض المحتوى")

def send_lecture_polls(chat_id, section, number):
    """إرسال اختبارات المحاضرة"""
    polls = data_manager.get_content(section, number, 'poll')
    if polls:
        bot.send_message(chat_id, f"📝 اختبار المحاضرة {number}:")
        sent_polls = False
        for poll in polls:
            try:
                try:
                    # محاولة إعادة توجيه الاستفتاء الأصلي
                    bot.forward_message(
                        chat_id,
                        poll['chat_id'],
                        poll['message_id']
                    )
                except:
                    # إذا فشل إعادة التوجيه، نرسل استفتاء جديد
                    bot.send_poll(
                        chat_id=chat_id,
                        question=poll['question'],
                        options=poll['options'],
                        type=poll['type'],
                        correct_option_id=poll['correct_option_id'],
                        is_anonymous=poll['is_anonymous'],
                        allows_multiple_answers=poll['allows_multiple_answers']
                    )
                sent_polls = True
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error sending poll: {e}")
        return sent_polls
    return False

@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    """معالجة الرسائل الصوتية"""
    try:
        if message.from_user.id != ADMIN_ID:
            return

        state = user_states.get_state(message.from_user.id)
        if state.get('state') != 'waiting_for_content':
            return

        section = state.get('section')
        number = state.get('number')

        audio_data = {
            'file_id': message.voice.file_id if message.voice else message.audio.file_id,
            'message_id': message.message_id,
            'chat_id': message.chat.id,
            'duration': message.voice.duration if message.voice else message.audio.duration,
            'type': 'voice' if message.voice else 'audio'
        }

        # حذف الشرح الصوتي القديم إذا وجد
        current_audio = data_manager.get_content(section, number, 'audio')
        if current_audio:
            bot.send_message(
                message.chat.id,
                "⚠️ يوجد شرح صوتي مسجل مسبقاً. سيتم استبداله بالشرح الجديد."
            )

        if data_manager.add_content(section, number, 'audio', audio_data):
            bot.reply_to(
                message,
                f"✅ تم حفظ الشرح الصوتي للمحاضرة {number} بنجاح\n\nهل تريد إضافة محتوى آخر؟",
                reply_markup=yes_no_keyboard
            )
            user_states.set_state(
                message.from_user.id,
                'waiting_for_answer',
                section=section,
                number=number
            )
        else:
            bot.reply_to(message, "❌ حدث خطأ في حفظ الملف الصوتي")

    except Exception as e:
        logger.error(f"Audio handler error: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في حفظ الملف الصوتي")

@bot.message_handler(content_types=['poll'])
def handle_poll(message):
    """معالجة الاستفتاءات"""
    try:
        if message.from_user.id != ADMIN_ID:
            return

        state = user_states.get_state(message.from_user.id)
        if state.get('state') != 'waiting_for_content':
            return

        poll_data = {
            'message_id': message.message_id,
            'chat_id': message.chat.id,
            'question': message.poll.question,
            'options': [option.text for option in message.poll.options],
            'correct_option_id': message.poll.correct_option_id,
            'type': message.poll.type,
            'is_anonymous': message.poll.is_anonymous,
            'allows_multiple_answers': message.poll.allows_multiple_answers
        }

        section = state.get('section')
        number = state.get('number')

        if data_manager.add_content(section, number, 'poll', poll_data):
            bot.send_message(
                message.chat.id,
                "✅ تم حفظ الاستفتاء بنجاح\n\nهل تريد إضافة المزيد؟",
                reply_markup=yes_no_keyboard
            )
            user_states.set_state(
                message.from_user.id,
                'waiting_for_answer',
                section=section,
                number=number
            )
        else:
            bot.reply_to(message, "❌ حدث خطأ في حفظ الاستفتاء")

    except Exception as e:
        logger.error(f"Poll handler error: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في حفظ الاستفتاء")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """معالجة جميع الرسائل النصية"""
    try:
        user_id = message.from_user.id
        text = message.text
        state = user_states.get_state(user_id)

        # معالجة زر الاختبار
        if text and text.startswith('اختبار المحاضرة '):
            number = text.split(' ')[2]
            section = state.get('section')
            if section and number:
                if not send_lecture_polls(message.chat.id, section, number):
                    bot.send_message(
                        message.chat.id,
                        "⚠️ لا يوجد اختبار لهذه المحاضرة"
                    )
            return

        # معالجة أوامر المدير
        if user_id == ADMIN_ID:
            if text == 'وضع المستخدم':
                user_states.set_state(user_id, 'main_menu', admin_mode=False)
                bot.send_message(
                    message.chat.id,
                    "تم التحويل إلى وضع المستخدم 👤",
                    reply_markup=create_main_keyboard()
                )
                return
            elif text == 'العودة لوضع المدير':
                user_states.set_state(user_id, 'admin_menu', admin_mode=True)
                bot.send_message(
                    message.chat.id,
                    "تم العودة إلى وضع المدير 👨‍💼",
                    reply_markup=create_admin_keyboard()
                )
                return
            elif text in ['إضافة شرح صوتي', 'إضافة اختبار']:
                content_type = 'audio' if text == 'إضافة شرح صوتي' else 'poll'
                bot.send_message(
                    message.chat.id,
                    "اختر القسم:",
                    reply_markup=create_main_keyboard()
                )
                user_states.set_state(
                    message.from_user.id,
                    'choosing_section',
                    content_type=content_type
                )
                return

        # معالجة اختيار القسم
        if text in ['نظم عملي', 'نظم نظري']:
            section = 'practical' if text == 'نظم عملي' else 'theoretical'
            keyboard = create_section_keyboard(section)
            
            if state.get('state') == 'choosing_section':
                bot.send_message(
                    message.chat.id,
                    "اختر المحاضرة:",
                    reply_markup=keyboard
                )
                user_states.set_state(
                    message.from_user.id,
                    'choosing_number',
                    section=section,
                    content_type=state.get('content_type')
                )
            else:
                bot.send_message(
                    message.chat.id,
                    "اختر المحاضرة:",
                    reply_markup=keyboard
                )
                user_states.set_state(
                    message.from_user.id,
                    'choosing_number',
                    section=section
                )
            return

        # معالجة اختيار المحاضرة
        elif text.startswith('محاضرة '):
            number = text.split(' ')[1]
            if number.isdigit():
                section = state.get('section')
                current_state = state.get('state')
                content_type = state.get('content_type')
                
                if user_id == ADMIN_ID and current_state == 'choosing_number' and content_type:
                    msg = "قم بإرسال الشرح الصوتي..." if content_type == 'audio' else "قم بإرسال الاستفتاء..."
                    bot.send_message(
                        message.chat.id,
                        msg,
                        reply_markup=types.ReplyKeyboardRemove()
                    )
                    user_states.set_state(
                        message.from_user.id,
                        'waiting_for_content',
                        section=section,
                        number=number,
                        content_type=content_type
                    )
                else:
                    show_lecture_content(message, section, number)
            return

        # معالجة الإجابات نعم/لا
        elif text in ['نعم', 'لا'] and state.get('state') == 'waiting_for_answer':
            section = state.get('section')
            content_type = state.get('content_type')
            if text == 'نعم':
                keyboard = create_section_keyboard(section)
                bot.send_message(
                    message.chat.id,
                    "اختر المحاضرة:",
                    reply_markup=keyboard
                )
                user_states.set_state(
                    message.from_user.id,
                    'choosing_number',
                    section=section,
                    content_type=content_type
                )
            else:
                bot.send_message(
                    message.chat.id,
                    "تم الانتهاء من إضافة المحتوى",
                    reply_markup=create_admin_keyboard()
                )
                user_states.clear_state(message.from_user.id)
            return

        # معالجة العودة للقائمة الرئيسية
        elif text == 'العودة للقائمة الرئيسية':
            keyboard = create_admin_keyboard() if (user_id == ADMIN_ID and state.get('admin_mode', True)) else create_main_keyboard()
            bot.send_message(
                message.chat.id,
                "تم العودة للقائمة الرئيسية",
                reply_markup=keyboard
            )
            user_states.clear_state(message.from_user.id)
            return

    except Exception as e:
        logger.error(f"Message handler error: {e}")
        bot.send_message(message.chat.id, "حدث خطأ، الرجاء المحاولة مرة أخرى.")

def main():
    """تشغيل البوت"""
    while True:
        try:
            logger.info("Bot started")
            print("جاري تشغيل البوت...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            print(f"حدث خطأ: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
