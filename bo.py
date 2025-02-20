import telebot
from telebot import types
import time
import json

# تهيئة البوت
bot = telebot.TeleBot('7748208067:AAEJ3urMl0dPS9Y3jVEkoIXsw8dKeshaXds')
ADMIN_ID = 7452139728

bot.set_my_description("""
🎓 بوت نظم المعلومات 

- قسمين رئيسيين:
📚 نظم نظري (11 محاضرة)
📝 نظم عملي (6 محاضرات)

✨ مميزات البوت:
• استفتاءات تفاعلية لكل محاضرة
• واجهة سهلة الاستخدام
• تصحيح فوري للإجابات
• متابعة تقدمك في المادة
• محتوى منظم حسب المحاضرات

📋 طريقة الاستخدام:
1. اختر القسم (نظري/عملي)
2. اختر رقم المحاضرة
3. حل الاستفتاءات
4. راجع إجاباتك

🔄 يتم تحديث المحتوى بشكل مستمر
""")

class DataManager:
    def __init__(self):
        self.data = {
            'practical': {str(i): {'polls': [], 'audio': []} for i in range(1, 7)},
            'theoretical': {str(i): {'polls': [], 'audio': []} for i in range(1, 12)}
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
                data_to_save = {
                    'data': self.data,
                    'stats': self.stats
                }
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                return True
        except Exception as e:
            print(f"Save data error: {e}")
            return False

    def load_data(self):
        try:
            with open('bot_data.json', 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                self.data = saved_data.get('data', self.data)
                self.stats = saved_data.get('stats', self.stats)
                return True
        except FileNotFoundError:
            self.save_data()
            return True
        except Exception as e:
            print(f"Load data error: {e}")
            return False

    def add_content(self, section, number, content_type, content_data):
        try:
            if section in self.data and number in self.data[section]:
                if content_type == 'poll':
                    if not all(key in content_data for key in ['question', 'options']):
                        return False
                    self.data[section][number]['polls'].append(content_data)
                    self.stats['total_polls'] += 1
                    self.stats[f'{section}_polls'] += 1
                elif content_type == 'audio':
                    if 'file_id' not in content_data:
                        return False
                    self.data[section][number]['audio'].append(content_data)
                    self.stats['total_audio'] += 1
                
                self.stats['last_update'] = time.strftime("%Y-%m-%d %H:%M:%S")
                self.save_data()
                return True
            return False
        except Exception as e:
            print(f"Add content error: {e}")
            return False

    def delete_content(self, section, number, content_type, index):
        try:
            content_list = self.data[section][number][f"{content_type}s"]
            if 0 <= index < len(content_list):
                content_list.pop(index)
                if content_type == 'poll':
                    self.stats['total_polls'] -= 1
                    self.stats[f'{section}_polls'] -= 1
                else:
                    self.stats['total_audio'] -= 1
                
                self.stats['last_update'] = time.strftime("%Y-%m-%d %H:%M:%S")
                return self.save_data()
            return False
        except Exception as e:
            print(f"Delete content error: {e}")
            return False

    def delete_all_content(self, section, number):
        try:
            if section in self.data and number in self.data[section]:
                polls_count = len(self.data[section][number]['polls'])
                self.stats['total_polls'] -= polls_count
                self.stats[f'{section}_polls'] -= polls_count
                self.data[section][number]['polls'] = []
                self.stats['last_update'] = time.strftime("%Y-%m-%d %H:%M:%S")
                return self.save_data()
            return False
        except Exception as e:
            print(f"Delete all content error: {e}")
            return False

    def get_content(self, section, number, content_type):
        try:
            return self.data[section][number][f"{content_type}s"]
        except Exception as e:
            print(f"Get content error: {e}")
            return []

class UserState:
    def __init__(self):
        self.states = {}

    def set_state(self, user_id, state, **kwargs):
        try:
            user_id = str(user_id)
            self.states[user_id] = {'state': state, 'admin_mode': True, **kwargs}
            return True
        except Exception as e:
            print(f"Set state error: {e}")
            return False

    def get_state(self, user_id):
        try:
            user_id = str(user_id)
            return self.states.get(user_id, {})
        except Exception as e:
            print(f"Get state error: {e}")
            return {}

    def clear_state(self, user_id):
        try:
            user_id = str(user_id)
            if user_id in self.states:
                admin_mode = self.states[user_id].get('admin_mode', True)
                self.states[user_id] = {'admin_mode': admin_mode}
            return True
        except Exception as e:
            print(f"Clear state error: {e}")
            return False

    def toggle_admin_mode(self, user_id):
        try:
            user_id = str(user_id)
            state = self.states.get(user_id, {})
            state['admin_mode'] = not state.get('admin_mode', True)
            self.states[user_id] = state
            return True
        except Exception as e:
            print(f"Toggle admin mode error: {e}")
            return False

# تهيئة القوائم
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_keyboard.add('نظم نظري', 'نظم عملي')

practical_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
practical_keyboard.add(*[f"محاضرة {i}" for i in range(1, 7)])
practical_keyboard.add('العودة للقائمة الرئيسية')

theoretical_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
theoretical_keyboard.add(*[f"محاضرة {i}" for i in range(1, 12)])
theoretical_keyboard.add('العودة للقائمة الرئيسية')

admin_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
admin_keyboard.add('إضافة محتوى', 'عرض المحتوى', 'حذف محتوى', 'وضع المستخدم', 'الإحصائيات')

admin_user_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
admin_user_keyboard.add('نظم نظري', 'نظم عملي', 'العودة لوضع المدير')

yes_no_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
yes_no_keyboard.add('نعم', 'لا')

def create_delete_markup(content_index, section, number, content_type):
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        delete_button = types.InlineKeyboardButton(
            "🗑 حذف",
            callback_data=f"delete_{content_type}_{section}_{number}_{content_index}"
        )
        delete_all_button = types.InlineKeyboardButton(
            "🗑 حذف جميع الاستفتاءات",
            callback_data=f"delete_all_{section}_{number}"
        )
        markup.add(delete_button)
        markup.add(delete_all_button)
        return markup
    except Exception as e:
        print(f"Create delete markup error: {e}")
        return None

# تهيئة المدراء
data_manager = DataManager()
user_states = UserState()
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        if user_id == ADMIN_ID:
            user_states.set_state(user_id, 'admin_menu')
            bot.send_message(
                message.chat.id,
                f"مرحباً {user_name}! 👋\n\nأنت في وضع المدير",
                reply_markup=admin_keyboard
            )
        else:
            user_states.set_state(user_id, 'main_menu', admin_mode=False)
            bot.send_message(
                message.chat.id,
                f"مرحباً {user_name}! 👋\n\nمرحباً بك في بوت نظم المعلومات",
                reply_markup=main_keyboard
            )
    except Exception as e:
        print(f"Start command error: {e}")
        bot.send_message(message.chat.id, "حدث خطأ، الرجاء المحاولة مرة أخرى /start")

@bot.message_handler(content_types=['poll'])
def handle_poll(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return

        state = user_states.get_state(message.from_user.id)
        if not state.get('state') == 'waiting_for_content':
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
        last_poll_time = state.get('last_poll_time', time.time())
        current_time = time.time()

        if data_manager.add_content(section, number, 'poll', poll_data):
            if not state.get('polls_added', False):
                user_states.set_state(
                    message.from_user.id,
                    'waiting_for_content',
                    section=section,
                    number=number,
                    last_poll_time=current_time,
                    last_poll_id=message.message_id,
                    polls_added=True
                )
                # انتظار لحظة للتحقق من اكتمال الإرسال
                time.sleep(2)
                bot.send_message(
                    message.chat.id,
                    "✅ تم حفظ الاستفتاءات بنجاح\n\nهل تريد إضافة المزيد؟",
                    reply_markup=yes_no_keyboard
                )
                user_states.set_state(
                    message.from_user.id,
                    'waiting_for_answer',
                    section=section,
                    number=number
                )

    except Exception as e:
        print(f"Poll handler error: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في حفظ الاستفتاء")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete_callback(call):
    try:
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "عذراً، هذا الخيار متاح للمدير فقط")
            return

        if call.data.startswith('delete_all_'):
            _, _, section, number = call.data.split('_')
            confirmation_markup = types.InlineKeyboardMarkup(row_width=2)
            yes_btn = types.InlineKeyboardButton(
                "✅ نعم، احذف الكل", 
                callback_data=f"confirm_delete_all_{section}_{number}"
            )
            no_btn = types.InlineKeyboardButton(
                "❌ إلغاء", 
                callback_data="cancel_delete_all"
            )
            confirmation_markup.add(yes_btn, no_btn)
            
            bot.edit_message_text(
                f"⚠️ هل أنت متأكد من حذف جميع الاستفتاءات في المحاضرة {number}؟\n\nهذا الإجراء لا يمكن التراجع عنه!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=confirmation_markup
            )
        else:
            _, content_type, section, number, index = call.data.split('_')
            if data_manager.delete_content(section, number, content_type, int(index)):
                bot.answer_callback_query(call.id, "تم الحذف بنجاح ✅")
                bot.edit_message_text(
                    "تم حذف المحتوى ✅",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
            else:
                bot.answer_callback_query(call.id, "حدث خطأ في الحذف ❌")
    except Exception as e:
        print(f"Delete callback error: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ ❌")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_delete_all_'))
def handle_confirm_delete_all(call):
    try:
        if call.from_user.id != ADMIN_ID:
            return

        _, _, _, section, number = call.data.split('_')
        if data_manager.delete_all_content(section, number):
            bot.answer_callback_query(call.id, "تم حذف جميع الاستفتاءات ✅")
            bot.edit_message_text(
                f"✅ تم حذف جميع الاستفتاءات من المحاضرة {number} بنجاح",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "حدث خطأ في الحذف ❌")
    except Exception as e:
        print(f"Confirm delete all error: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ ❌")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete_all")
def handle_cancel_delete_all(call):
    try:
        bot.answer_callback_query(call.id, "تم إلغاء عملية الحذف")
        bot.edit_message_text(
            "تم إلغاء عملية الحذف ❌",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    except Exception as e:
        print(f"Cancel delete all error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    try:
        user_id = message.from_user.id
        text = message.text
        state = user_states.get_state(user_id)

        if user_id == ADMIN_ID:
            if text == 'وضع المستخدم':
                user_states.toggle_admin_mode(user_id)
                bot.send_message(message.chat.id, "تم التحويل إلى وضع المستخدم 👤", 
                               reply_markup=admin_user_keyboard)
                return

            elif text == 'العودة لوضع المدير':
                user_states.toggle_admin_mode(user_id)
                bot.send_message(message.chat.id, "تم العودة إلى وضع المدير 👨‍💼", 
                               reply_markup=admin_keyboard)
                return

            elif text == 'الإحصائيات':
                show_stats(message)
                return

            elif text == 'إضافة محتوى':
                bot.send_message(message.chat.id, "اختر القسم:", reply_markup=main_keyboard)
                user_states.set_state(message.from_user.id, 'choosing_section')
                return

            elif text == 'عرض المحتوى':
                bot.send_message(message.chat.id, "اختر القسم:", reply_markup=main_keyboard)
                user_states.set_state(message.from_user.id, 'choosing_section_to_view')
                return

            elif text == 'حذف محتوى':
                bot.send_message(message.chat.id, "اختر القسم:", reply_markup=main_keyboard)
                user_states.set_state(message.from_user.id, 'choosing_section_to_delete')
                return

        if text in ['نظم عملي', 'نظم نظري']:
            section = 'practical' if text == 'نظم عملي' else 'theoretical'
            keyboard = practical_keyboard if section == 'practical' else theoretical_keyboard
            current_state = state.get('state', '')

            if current_state == 'choosing_section':
                bot.send_message(message.chat.id, "اختر المحاضرة:", reply_markup=keyboard)
                user_states.set_state(message.from_user.id, 'choosing_number', section=section)
            elif current_state == 'choosing_section_to_view':
                bot.send_message(message.chat.id, "اختر المحاضرة:", reply_markup=keyboard)
                user_states.set_state(message.from_user.id, 'choosing_number_to_view', section=section)
            elif current_state == 'choosing_section_to_delete':
                bot.send_message(message.chat.id, "اختر المحاضرة:", reply_markup=keyboard)
                user_states.set_state(message.from_user.id, 'choosing_number_to_delete', section=section)
            else:
                bot.send_message(message.chat.id, "اختر المحاضرة:", reply_markup=keyboard)
                user_states.set_state(message.from_user.id, 'choosing_number', 
                                    section=section, admin_mode=False)
            return

        elif text.startswith('محاضرة '):
            number = text.split(' ')[1]
            if number.isdigit() and state.get('state'):
                current_state = state.get('state')
                section = state.get('section')
                
                if current_state == 'choosing_number':
                    bot.send_message(
                        message.chat.id,
                        "قم بإرسال الاستفتاءات...",
                        reply_markup=types.ReplyKeyboardRemove()
                    )
                    user_states.set_state(message.from_user.id, 'waiting_for_content',
                                        section=section, number=number)
                elif current_state == 'choosing_number_to_view':
                    show_content(message, section, number)
                elif current_state == 'choosing_number_to_delete':
                    show_content_with_delete_buttons(message, section, number)
                else:
                    show_content(message, section, number)
            return

        elif text in ['نعم', 'لا'] and state.get('state') == 'waiting_for_answer':
            section = state.get('section')
            if text == 'نعم':
                keyboard = practical_keyboard if section == 'practical' else theoretical_keyboard
                bot.send_message(message.chat.id, "اختر المحاضرة:", reply_markup=keyboard)
                user_states.set_state(message.from_user.id, 'choosing_number', section=section)
            else:
                bot.send_message(message.chat.id, "تم الانتهاء من إضافة المحتوى", 
                               reply_markup=admin_keyboard)
                user_states.clear_state(message.from_user.id)
            return

        elif text == 'العودة للقائمة الرئيسية':
            keyboard = admin_keyboard if (user_id == ADMIN_ID and state.get('admin_mode', True)) else main_keyboard
            bot.send_message(message.chat.id, "تم العودة للقائمة الرئيسية", 
                           reply_markup=keyboard)
            user_states.clear_state(message.from_user.id)
            return

    except Exception as e:
        print(f"Message handler error: {e}")
        bot.send_message(message.chat.id, "حدث خطأ، الرجاء المحاولة مرة أخرى.")

def show_content(message, section, number):
    try:
        polls = data_manager.get_content(section, number, 'poll')
        if not polls:
            bot.send_message(message.chat.id, "لا يوجد محتوى في هذه المحاضرة")
            return

        bot.send_message(message.chat.id, f"استفتاءات المحاضرة {number}:")
        for poll in polls:
            try:
                bot.forward_message(
                    message.chat.id,
                    poll['chat_id'],
                    poll['message_id']
                )
            except Exception as e:
                print(f"Error forwarding poll: {e}")
                try:
                    bot.send_poll(
                        chat_id=message.chat.id,
                        question=poll['question'],
                        options=poll['options'],
                        type=poll['type'],
                        correct_option_id=poll['correct_option_id'],
                        is_anonymous=poll['is_anonymous'],
                        allows_multiple_answers=poll['allows_multiple_answers']
                    )
                except Exception as e:
                    print(f"Error sending poll: {e}")
            time.sleep(0.5)

    except Exception as e:
        print(f"Show content error: {e}")

def show_content_with_delete_buttons(message, section, number):
    try:
        polls = data_manager.get_content(section, number, 'poll')
        if not polls:
            bot.send_message(message.chat.id, "لا يوجد محتوى في هذه المحاضرة")
            return

        bot.send_message(message.chat.id, f"استفتاءات المحاضرة {number}:")
        for index, poll in enumerate(polls):
            try:
                sent_msg = bot.forward_message(
                    message.chat.id,
                    poll['chat_id'],
                    poll['message_id']
                )
                bot.send_message(
                    message.chat.id,
                    f"استفتاء رقم {index + 1}",
                    reply_markup=create_delete_markup(index, section, number, 'poll')
                )
            except Exception as e:
                print(f"Error showing poll for deletion: {e}")
                try:
                    sent_poll = bot.send_poll(
                        chat_id=message.chat.id,
                        question=poll['question'],
                        options=poll['options'],
                        type=poll['type'],
                        correct_option_id=poll['correct_option_id'],
                        is_anonymous=poll['is_anonymous'],
                        allows_multiple_answers=poll['allows_multiple_answers']
                    )
                    bot.send_message(
                        message.chat.id,
                        f"استفتاء رقم {index + 1}",
                        reply_markup=create_delete_markup(index, section, number, 'poll')
                    )
                except Exception as e:
                    print(f"Error sending poll for deletion: {e}")
            time.sleep(0.5)

    except Exception as e:
        print(f"Show content with delete buttons error: {e}")

def show_stats(message):
    try:
        stats = data_manager.stats
        text = "*📊 إحصائيات المحتوى:*\n\n"
        text += f"📊 إجمالي الاستفتاءات: {stats['total_polls']}\n"
        text += f"📚 استفتاءات نظم عملي: {stats['practical_polls']}\n"
        text += f"📖 استفتاءات نظم نظري: {stats['theoretical_polls']}\n"
        if stats['last_update']:
            text += f"\nآخر تحديث: {stats['last_update']}"
        
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Show stats error: {e}")

def main():
    while True:
        try:
            print("جاري تشغيل البوت...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()