import logging
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio
import json
import os
import random
from datetime import datetime

class Bot:
    def __init__(self):
        self.token = "7541711169:AAHzgD3QntYV7qGz_HiyttOrLC_TjaYm_ZQ"
        self.admin_id = 7452139728
        self.bot = AsyncTeleBot(self.token)
        
        # تهيئة المتغيرات الأساسية
        self.user_state = {}
        self.admin_view = {}
        self.menu_messages = {}
        self.temp_data = {}
        self.last_activity = {}
        
        # تهيئة هيكل البيانات
        self.initialize_data()
        self.setup_handlers()

    def initialize_data(self):
        """تهيئة هيكل البيانات الأساسي"""
        self.menus = {
            "course_info": {
                "name": "حقوق الإنسان",
                "summary": {
                    "content": []  # للملفات والصور والفيديوهات
                },
                "quizzes": {
                    "parts": {
                        "الجزء الأول 📘": {"questions": [], "total": 0},
                        "الجزء الثاني 📗": {"questions": [], "total": 0},
                        "الجزء الثالث 📙": {"questions": [], "total": 0},
                        "الجزء الرابع 📕": {"questions": [], "total": 0},
                        "الجزء الخامس 📓": {"questions": [], "total": 0}
                    },
                    "total_questions": 0,
                    "last_update": None
                }
            }
        }
        self.load_data()

    def setup_handlers(self):
        """إعداد معالجات الرسائل"""
        @self.bot.message_handler(commands=['start'])
        async def start_command(message):
            await self.start_handler(message)

        @self.bot.message_handler(content_types=['document', 'photo', 'video'])
        async def media_command(message):
            await self.handle_media(message)

        @self.bot.message_handler(content_types=['text'])
        async def handle_text(message):
            await self.text_handler(message)

    def load_data(self):
        """تحميل البيانات من الملف"""
        try:
            if os.path.exists('menus.json'):
                with open('menus.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "course_info" in data:
                        self.menus = data
            print("✅ تم تحميل البيانات")
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {e}")

    def save_data(self):
        """حفظ البيانات في الملف"""
        try:
            with open('menus.json', 'w', encoding='utf-8') as f:
                json.dump(self.menus, f, ensure_ascii=False, indent=2)
            print("✅ تم حفظ البيانات")
            return True
        except Exception as e:
            print(f"❌ خطأ في حفظ البيانات: {e}")
            return False

    async def clean_all_messages(self, chat_id):
        """حذف جميع رسائل البوت السابقة"""
        try:
            if chat_id in self.menu_messages:
                for msg_type, messages in self.menu_messages[chat_id].items():
                    for msg_id in messages:
                        try:
                            await self.bot.delete_message(chat_id, msg_id)
                        except Exception as e:
                            print(f"خطأ في حذف الرسالة {msg_id}: {e}")
                self.menu_messages[chat_id] = {}
        except Exception as e:
            print(f"خطأ في حذف الرسائل: {e}")

    async def send_and_store(self, chat_id, text, reply_markup=None, menu_type=None):
        """إرسال وتخزين الرسائل"""
        try:
            message = await self.bot.send_message(
                chat_id,
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            if menu_type:
                if chat_id not in self.menu_messages:
                    self.menu_messages[chat_id] = {}
                if menu_type not in self.menu_messages[chat_id]:
                    self.menu_messages[chat_id][menu_type] = []
                self.menu_messages[chat_id][menu_type].append(message.message_id)
            return message
        except Exception as e:
            print(f"Error in send_and_store: {e}")
            return None

    async def backup_data(self):
        """عمل نسخة احتياطية من البيانات"""
        try:
            backup_file = f'backup_menus_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.menus, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error in backup_data: {e}")
            return False
    async def handle_quiz_file(self, chat_id, file_content):
        """معالجة ملف الأسئلة وإضافتها"""
        try:
            print("⏳ بدء معالجة ملف الأسئلة...")
            
            # تحليل الأسئلة من الملف
            questions = []
            current_question = None
            current_options = []
            
            for line in file_content.split('\n'):
                line = line.strip()
                if not line and current_question:
                    if len(current_options) >= 2:
                        questions.append({
                            'question': current_question,
                            'options': current_options.copy(),
                            'timestamp': datetime.now().isoformat()
                        })
                        print(f"✅ تم إضافة سؤال: {current_question}")
                    current_question = None
                    current_options = []
                    continue
                
                if line:
                    if not current_question:
                        current_question = line
                    else:
                        is_correct = '✓' in line
                        option = line.replace('✓', '').strip()
                        if is_correct:
                            current_options.insert(0, option)
                            print(f"💡 إجابة صحيحة: {option}")
                        else:
                            current_options.append(option)
                            print(f"📝 خيار: {option}")

            # إضافة السؤال الأخير إذا وجد
            if current_question and len(current_options) >= 2:
                questions.append({
                    'question': current_question,
                    'options': current_options,
                    'timestamp': datetime.now().isoformat()
                })

            if not questions:
                await self.send_and_store(
                    chat_id,
                    "❌ لم يتم العثور على أسئلة صالحة في الملف",
                    menu_type='error'
                )
                return

            # توزيع الأسئلة على الأجزاء
            total = len(questions)
            per_part = max(1, total // 5)
            
            quiz_parts = self.menus["course_info"]["quizzes"]["parts"]
            for i, (part_name, part_data) in enumerate(quiz_parts.items()):
                start_idx = i * per_part
                end_idx = start_idx + per_part if i < 4 else total
                part_questions = questions[start_idx:end_idx]
                
                # تحديث بيانات الجزء
                part_data["questions"] = [{
                    'question': q['question'],
                    'options': q['options'],
                    'correct_answer': q['options'][0],
                    'timestamp': q['timestamp']
                } for q in part_questions]
                part_data["total"] = len(part_questions)

            # تحديث إجمالي الأسئلة والوقت
            self.menus["course_info"]["quizzes"]["total_questions"] = total
            self.menus["course_info"]["quizzes"]["last_update"] = datetime.now().isoformat()

            # حفظ البيانات
            if self.save_data() and await self.backup_data():
                # إرسال تأكيد
                msg = "✅ تم حفظ الأسئلة بنجاح\n\n"
                msg += f"📊 إجمالي الأسئلة: {total}\n"
                msg += "➖" * 15 + "\n"
                
                for part_name, part_data in quiz_parts.items():
                    msg += f"{part_name}: {part_data['total']} سؤال\n"

                await self.clean_all_messages(chat_id)
                await self.send_and_store(chat_id, msg, menu_type='success')
                return await self.show_admin_menu(chat_id)
            else:
                raise Exception("فشل في حفظ البيانات")

        except Exception as e:
            print(f"❌ خطأ في معالجة ملف الأسئلة: {str(e)}")
            await self.send_and_store(
                chat_id,
                "❌ حدث خطأ في معالجة الملف\n"
                "تأكد من صحة تنسيق الملف وحاول مرة أخرى",
                menu_type='error'
            )
            return await self.show_admin_menu(chat_id)

    async def show_quiz_parts_menu(self, chat_id):
        """عرض قائمة أجزاء الاختبار"""
        try:
            await self.clean_all_messages(chat_id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            
            parts = [
                ["📘 الجزء الأول", "📗 الجزء الثاني"],
                ["📙 الجزء الثالث", "📕 الجزء الرابع"],
                ["📓 الجزء الخامس"],
                ["🔙 رجوع للقائمة الرئيسية"]
            ]
            
            for row in parts:
                keyboard.add(*row)
            
            parts_info = (
                "📝 <b>اختبارات مادة حقوق الإنسان</b>\n\n"
                "اختر الجزء الذي تريد اختباره:\n\n"
            )

            quiz_data = self.menus["course_info"]["quizzes"]
            total = quiz_data["total_questions"]
            
            if total > 0:
                parts_info += f"📊 إجمالي الأسئلة: {total}\n"
                parts_info += "➖" * 15 + "\n\n"
                
                for part_name, part_data in quiz_data["parts"].items():
                    parts_info += f"{part_name}: {part_data['total']} سؤال\n"
                
                last_update = datetime.fromisoformat(quiz_data["last_update"])
                parts_info += f"\n🕒 آخر تحديث: {last_update.strftime('%Y-%m-%d %H:%M')}"
            else:
                parts_info += "⚠️ لا توجد أسئلة متوفرة حالياً\n"
            
            parts_info += "\n\n💡 سيتم خلط الأسئلة في كل مرة"
            
            await self.send_and_store(
                chat_id,
                parts_info,
                reply_markup=keyboard,
                menu_type='quiz_parts'
            )
        except Exception as e:
            print(f"❌ خطأ في عرض قائمة الأجزاء: {e}")
            await self.show_user_menu(chat_id)

    async def show_quiz_questions(self, chat_id, part_name):
        """عرض أسئلة جزء معين"""
        try:
            quiz_parts = self.menus["course_info"]["quizzes"]["parts"]
            full_part_name = next((name for name in quiz_parts.keys() if part_name in name), None)
            
            if not full_part_name or not quiz_parts[full_part_name]["questions"]:
                await self.send_and_store(
                    chat_id,
                    "⚠️ لا توجد أسئلة متوفرة في هذا الجزء",
                    menu_type='info'
                )
                return

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("❌ إنهاء الاختبار", "🔙 رجوع للأجزاء")
            
            await self.send_and_store(
                chat_id,
                f"{full_part_name}\n\n"
                f"📊 عدد الأسئلة: {quiz_parts[full_part_name]['total']}\n"
                "🔄 الأسئلة عشوائية\n"
                "✨ ستظهر الإجابة الصحيحة بعد كل سؤال\n\n"
                "🎯 حظاً موفقاً!",
                reply_markup=keyboard,
                menu_type='quiz_questions'
            )
            
            # خلط الأسئلة
            questions = quiz_parts[full_part_name]["questions"].copy()
            random.shuffle(questions)
            
            for i, question in enumerate(questions, 1):
                options = question['options'].copy()
                correct_answer = question['correct_answer']
                random.shuffle(options)
                correct_index = options.index(correct_answer)
                
                msg = await self.bot.send_poll(
                    chat_id=chat_id,
                    question=f"❓ السؤال {i}/{len(questions)}:\n\n{question['question']}",
                    options=options,
                    type='quiz',
                    correct_option_id=correct_index,
                    is_anonymous=False,
                    explanation=f"💡 الإجابة الصحيحة: {correct_answer}"
                )
                
                if 'quiz_questions' not in self.menu_messages.get(chat_id, {}):
                    self.menu_messages[chat_id] = {'quiz_questions': []}
                self.menu_messages[chat_id]['quiz_questions'].append(msg.message_id)
                await asyncio.sleep(0.5)

        except Exception as e:
            print(f"❌ خطأ في عرض الأسئلة: {e}")
            await self.show_quiz_parts_menu(chat_id)

    async def delete_quiz_content(self, chat_id, part_name=None):
        """حذف محتوى الأسئلة"""
        try:
            quiz_data = self.menus["course_info"]["quizzes"]
            
            if part_name:
                # حذف جزء محدد
                if part_name in quiz_data["parts"]:
                    quiz_data["parts"][part_name]["questions"] = []
                    quiz_data["parts"][part_name]["total"] = 0
                    msg = f"✅ تم حذف أسئلة {part_name} بنجاح"
            else:
                # حذف كل الأسئلة
                for part_data in quiz_data["parts"].values():
                    part_data["questions"] = []
                    part_data["total"] = 0
                quiz_data["total_questions"] = 0
                quiz_data["last_update"] = datetime.now().isoformat()
                msg = "✅ تم حذف جميع الأسئلة بنجاح"

            if self.save_data():
                await self.clean_all_messages(chat_id)
                await self.send_and_store(
                    chat_id,
                    msg,
                    menu_type='success'
                )
                return True
            else:
                raise Exception("فشل في حفظ البيانات")

        except Exception as e:
            print(f"❌ خطأ في حذف الأسئلة: {e}")
            await self.send_and_store(
                chat_id,
                "❌ حدث خطأ أثناء حذف الأسئلة",
                menu_type='error'
            )
            return False
    async def start_handler(self, message):
        """معالج أمر البداية"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            first_name = message.from_user.first_name

            await self.clean_all_messages(chat_id)

            if user_id == self.admin_id:
                welcome_text = (
                    f"👋 <b>مرحباً {first_name}</b>\n\n"
                    "🎓 <b>لوحة تحكم بوت حقوق الإنسان</b>\n\n"
                    "🔸 يمكنك إدارة المحتوى من خلال:\n\n"
                    "📚 <b>إضافة للملخص:</b>\n"
                    "• رفع ملفات PDF 📄\n"
                    "• إضافة صور توضيحية 🖼\n"
                    "• مقاطع فيديو تعليمية 🎥\n\n"
                    "📝 <b>إضافة أسئلة:</b>\n"
                    "• رفع ملف الأسئلة النصي\n"
                    "• سيتم تقسيمها إلى 5 أجزاء تلقائياً\n"
                    "• يتم خلط الأسئلة في كل مرة\n\n"
                    "👥 <b>وضع المستخدم:</b>\n"
                    "• معاينة البوت كمستخدم عادي\n\n"
                    "✨ <b>ابدأ الآن باختيار أحد الخيارات أدناه</b>"
                )
                self.admin_view[chat_id] = 'admin'
                await self.show_admin_menu(chat_id, welcome_text)
            else:
                welcome_text = (
                    f"🌟 <b>مرحباً {first_name}</b>\n\n"
                    "📚 أهلاً بك في بوت حقوق الإنسان\n\n"
                    "يمكنك من خلال هذا البوت:\n"
                    "• مراجعة ملخص المادة 📖\n"
                    "• حل الأسئلة والاختبارات ✍️\n"
                    "• التعلم بطريقة تفاعلية 🎯\n\n"
                    "🔍 <b>للبدء، اختر من القائمة أدناه:</b>"
                )
                await self.show_user_menu(chat_id, welcome_text)
        except Exception as e:
            print(f"Error in start_handler: {e}")

    async def show_admin_menu(self, chat_id, welcome_message=None):
        """عرض قائمة المشرف"""
        try:
            await self.clean_all_messages(chat_id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            buttons = [
                "📚 إضافة للملخص",
                "📝 إضافة أسئلة",
                "🗑️ حذف محتوى",
                "👥 وضع المستخدم",
                "📊 إحصائيات البوت"
            ]
            keyboard.add(*buttons)
            
            if welcome_message:
                await self.send_and_store(
                    chat_id,
                    welcome_message,
                    reply_markup=keyboard,
                    menu_type='admin'
                )
            else:
                await self.send_and_store(
                    chat_id,
                    "🎛 <b>لوحة التحكم</b>\n"
                    "اختر الإجراء المطلوب:",
                    reply_markup=keyboard,
                    menu_type='admin'
                )
        except Exception as e:
            print(f"Error in show_admin_menu: {e}")

    async def show_user_menu(self, chat_id, welcome_message=None):
        """عرض قائمة المستخدم"""
        try:
            await self.clean_all_messages(chat_id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("📚 ملخص المادة")
            keyboard.add("📝 اختبارات المادة")
            
            if chat_id == self.admin_id and self.admin_view.get(chat_id) == 'user':
                keyboard.add("🔄 رجوع لوضع المشرف")
            
            if welcome_message:
                await self.send_and_store(
                    chat_id,
                    welcome_message,
                    reply_markup=keyboard,
                    menu_type='user'
                )
            else:
                await self.send_and_store(
                    chat_id,
                    "🎯 <b>القائمة الرئيسية</b>\n"
                    "اختر ما تريد مراجعته:",
                    reply_markup=keyboard,
                    menu_type='user'
                )
        except Exception as e:
            print(f"Error in show_user_menu: {e}")

    async def show_delete_menu(self, chat_id):
        """عرض قائمة الحذف"""
        try:
            await self.clean_all_messages(chat_id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            
            buttons = [
                "🗑️ حذف جميع الأسئلة",
                "🗑️ حذف الملخص",
                "🗑️ حذف جزء محدد",
                "🔙 رجوع"
            ]
            keyboard.add(*buttons)
            
            await self.send_and_store(
                chat_id,
                "⚠️ <b>حذف المحتوى</b>\n\n"
                "اختر نوع المحتوى الذي تريد حذفه:\n\n"
                "• حذف جميع الأسئلة من كل الأجزاء\n"
                "• حذف محتوى الملخص\n"
                "• حذف جزء محدد من الأسئلة\n\n"
                "⚠️ <b>تنبيه:</b> لا يمكن التراجع عن عملية الحذف!",
                reply_markup=keyboard,
                menu_type='delete_menu'
            )
        except Exception as e:
            print(f"Error in show_delete_menu: {e}")

    async def show_stats(self, chat_id):
        """عرض إحصائيات البوت"""
        try:
            quiz_data = self.menus["course_info"]["quizzes"]
            summary_data = self.menus["course_info"]["summary"]
            
            stats = "📊 <b>إحصائيات البوت</b>\n\n"
            
            # إحصائيات الأسئلة
            stats += "📝 <b>الأسئلة:</b>\n"
            stats += f"• إجمالي الأسئلة: {quiz_data['total_questions']}\n"
            for part_name, part_data in quiz_data["parts"].items():
                stats += f"• {part_name}: {part_data['total']} سؤال\n"
            
            # إحصائيات الملخص
            stats += "\n📚 <b>الملخص:</b>\n"
            files_count = len([item for item in summary_data["content"] if item["file_type"] == "document"])
            photos_count = len([item for item in summary_data["content"] if item["file_type"] == "photo"])
            videos_count = len([item for item in summary_data["content"] if item["file_type"] == "video"])
            
            stats += f"• ملفات PDF: {files_count}\n"
            stats += f"• صور: {photos_count}\n"
            stats += f"• فيديوهات: {videos_count}\n"
            
            # آخر تحديث
            if quiz_data["last_update"]:
                last_update = datetime.fromisoformat(quiz_data["last_update"])
                stats += f"\n🕒 آخر تحديث: {last_update.strftime('%Y-%m-%d %H:%M')}"
            
            await self.clean_all_messages(chat_id)
            await self.send_and_store(
                chat_id,
                stats,
                menu_type='stats'
            )
            
        except Exception as e:
            print(f"Error in show_stats: {e}")
            await self.send_and_store(
                chat_id,
                "❌ حدث خطأ في عرض الإحصائيات",
                menu_type='error'
            )

    async def text_handler(self, message):
        """معالج الرسائل النصية"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            text = message.text

            # معالجة أوامر المشرف
            if user_id == self.admin_id:
                if text == "📚 إضافة للملخص":
                    self.user_state[chat_id] = 'waiting_summary_content'
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    keyboard.add("🔙 رجوع")
                    await self.send_and_store(
                        chat_id,
                        "📤 <b>إضافة محتوى للملخص</b>\n\n"
                        "يمكنك إرسال:\n"
                        "• صور توضيحية 🖼\n"
                        "• مقاطع فيديو 🎥\n"
                        "• ملفات PDF 📄\n\n"
                        "✨ سيتم إضافة الملفات تلقائياً إلى الملخص",
                        reply_markup=keyboard,
                        menu_type='waiting_files'
                    )
                    return

                elif text == "📝 إضافة أسئلة":
                    self.user_state[chat_id] = 'waiting_quiz_file'
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    keyboard.add("🔙 رجوع")
                    await self.send_and_store(
                        chat_id,
                        "📝 <b>إضافة ملف الأسئلة</b>\n\n"
                        "📋 <u>تنسيق الملف المطلوب:</u>\n"
                        "<code>السؤال\n"
                        "الإجابة الصحيحة✓\n"
                        "إجابة خاطئة\n"
                        "إجابة خاطئة\n"
                        "إجابة خاطئة</code>\n\n"
                        "✨ <b>ملاحظات هامة:</b>\n"
                        "• ضع علامة (✓) بعد الإجابة الصحيحة\n"
                        "• اترك سطر فارغ بين كل سؤال وآخر\n"
                        "• سيتم تقسيم الأسئلة تلقائياً\n"
                        "• يتم خلط الأسئلة في كل مرة",
                        reply_markup=keyboard,
                        menu_type='waiting_quiz'
                    )
                    return

                elif text == "🗑️ حذف محتوى":
                    return await self.show_delete_menu(chat_id)
                
                elif text == "📊 إحصائيات البوت":
                    return await self.show_stats(chat_id)

                elif text.startswith("🗑️ حذف"):
                    if text == "🗑️ حذف جميع الأسئلة":
                        await self.delete_quiz_content(chat_id)
                    elif text == "🗑️ حذف الملخص":
                        await self.delete_summary_content(chat_id)
                    elif text == "🗑️ حذف جزء محدد":
                        await self.show_parts_for_deletion(chat_id)
                    return await self.show_delete_menu(chat_id)

                elif text == "👥 وضع المستخدم":
                    self.admin_view[chat_id] = 'user'
                    return await self.show_user_menu(chat_id)

                elif text == "🔄 رجوع لوضع المشرف":
                    self.admin_view[chat_id] = 'admin'
                    return await self.show_admin_menu(chat_id)

            # معالجة أوامر المستخدم
            if text == "📚 ملخص المادة":
                return await self.show_summary(chat_id)
            elif text == "📝 اختبارات المادة":
                return await self.show_quiz_parts_menu(chat_id)
            elif "الجزء" in text:
                part_name = text.replace("📘 ", "").replace("📗 ", "").replace("📙 ", "").replace("📕 ", "").replace("📓 ", "")
                return await self.show_quiz_questions(chat_id, part_name)

            # معالجة أزرار الرجوع
            elif text in ["❌ إنهاء الاختبار", "❌ إنهاء المراجعة", "🔙 رجوع للأجزاء"]:
                await self.clean_all_messages(chat_id)
                if "رجوع للأجزاء" in text:
                    return await self.show_quiz_parts_menu(chat_id)
                return await self.show_user_menu(chat_id)

            elif text == "🔙 رجوع للقائمة الرئيسية":
                await self.clean_all_messages(chat_id)
                return await self.show_user_menu(chat_id)

            elif text == "🔙 رجوع":
                await self.clean_all_messages(chat_id)
                if user_id == self.admin_id and self.admin_view.get(chat_id) == 'admin':
                    self.user_state[chat_id] = 'main'
                    return await self.show_admin_menu(chat_id)
                else:
                    return await self.show_user_menu(chat_id)

        except Exception as e:
            print(f"Error in text_handler: {e}")
            if user_id == self.admin_id:
                await self.show_admin_menu(chat_id)
            else:
                await self.show_user_menu(chat_id)
    async def handle_media(self, message):
        """معالجة الملفات المرفوعة"""
        try:
            chat_id = message.chat.id
            if chat_id != self.admin_id:
                return

            # معالجة ملف الأسئلة
            if message.document and message.document.file_name.endswith('.txt'):
                if self.user_state.get(chat_id) == 'waiting_quiz_file':
                    try:
                        file_info = await self.bot.get_file(message.document.file_id)
                        downloaded_file = await self.bot.download_file(file_info.file_path)
                        file_content = downloaded_file.decode('utf-8')
                        await self.handle_quiz_file(chat_id, file_content)
                    except Exception as e:
                        print(f"Error downloading file: {e}")
                        await self.send_and_store(
                            chat_id,
                            "❌ حدث خطأ في تحميل الملف",
                            menu_type='error'
                        )
                    return

            # معالجة محتوى الملخص
            if self.user_state.get(chat_id) == 'waiting_summary_content':
                file_data = {
                    'file_id': None,
                    'file_type': None,
                    'file_name': None,
                    'timestamp': datetime.now().isoformat()
                }
                
                if message.photo:
                    file_data.update({
                        'file_id': message.photo[-1].file_id,
                        'file_type': 'photo'
                    })
                elif message.video:
                    file_data.update({
                        'file_id': message.video.file_id,
                        'file_type': 'video',
                        'file_name': message.video.file_name if hasattr(message.video, 'file_name') else None
                    })
                elif message.document:
                    file_data.update({
                        'file_id': message.document.file_id,
                        'file_type': 'document',
                        'file_name': message.document.file_name
                    })
                
                if file_data['file_id']:
                    self.menus["course_info"]["summary"]["content"].append(file_data)
                    if self.save_data():
                        msg = "✅ تم حفظ الملف في الملخص"
                        if file_data['file_name']:
                            msg += f"\nاسم الملف: {file_data['file_name']}"
                        await self.send_and_store(
                            chat_id,
                            msg,
                            menu_type='success'
                        )
                    else:
                        await self.send_and_store(
                            chat_id,
                            "❌ حدث خطأ في حفظ الملف",
                            menu_type='error'
                        )
                
        except Exception as e:
            print(f"Error in handle_media: {e}")
            await self.send_and_store(
                chat_id,
                "❌ حدث خطأ في معالجة الملف",
                menu_type='error'
            )

    async def show_summary(self, chat_id):
        """عرض محتوى الملخص"""
        try:
            await self.clean_all_messages(chat_id)
            content = self.menus["course_info"]["summary"]["content"]
            
            if not content:
                await self.send_and_store(
                    chat_id,
                    "⚠️ لا يوجد محتوى متاح حالياً في الملخص",
                    menu_type='info'
                )
                return

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("❌ إنهاء المراجعة")
            
            await self.send_and_store(
                chat_id,
                "📚 <b>ملخص مادة حقوق الإنسان</b>\n\n"
                "📎 المحتوى المتوفر:\n"
                "• ملفات PDF\n"
                "• صور توضيحية\n"
                "• مقاطع فيديو\n\n"
                "⏳ جاري إرسال الملفات...",
                reply_markup=keyboard,
                menu_type='summary_files'
            )
            
            for item in content:
                try:
                    caption = f"📅 تاريخ الإضافة: {datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M')}"
                    if item['file_name']:
                        caption += f"\n📄 اسم الملف: {item['file_name']}"
                    
                    if item['file_type'] == 'photo':
                        msg = await self.bot.send_photo(chat_id, item['file_id'], caption=caption)
                    elif item['file_type'] == 'video':
                        msg = await self.bot.send_video(chat_id, item['file_id'], caption=caption)
                    elif item['file_type'] == 'document':
                        msg = await self.bot.send_document(chat_id, item['file_id'], caption=caption)
                    
                    if 'summary_files' not in self.menu_messages.get(chat_id, {}):
                        self.menu_messages[chat_id] = {'summary_files': []}
                    self.menu_messages[chat_id]['summary_files'].append(msg.message_id)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Error sending file: {e}")
            
            await self.send_and_store(
                chat_id,
                "✅ تم إرسال جميع الملفات\n"
                "يمكنك الخروج عند الانتهاء من المراجعة",
                menu_type='summary_end'
            )

        except Exception as e:
            print(f"Error in show_summary: {e}")
            await self.show_user_menu(chat_id)

    async def delete_summary_content(self, chat_id):
        """حذف محتوى الملخص"""
        try:
            self.menus["course_info"]["summary"]["content"] = []
            if self.save_data():
                await self.send_and_store(
                    chat_id,
                    "✅ تم حذف محتوى الملخص بنجاح",
                    menu_type='success'
                )
            else:
                raise Exception("فشل في حفظ البيانات")
        except Exception as e:
            print(f"Error in delete_summary_content: {e}")
            await self.send_and_store(
                chat_id,
                "❌ حدث خطأ أثناء حذف المحتوى",
                menu_type='error'
            )

    async def show_parts_for_deletion(self, chat_id):
        """عرض قائمة الأجزاء للحذف"""
        try:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            quiz_parts = self.menus["course_info"]["quizzes"]["parts"]
            
            buttons = []
            for part_name, part_data in quiz_parts.items():
                if part_data["total"] > 0:
                    buttons.append(f"حذف {part_name}")
            
            if buttons:
                keyboard.add(*buttons)
                keyboard.add("🔙 رجوع")
                
                await self.send_and_store(
                    chat_id,
                    "🗑️ اختر الجزء الذي تريد حذفه:",
                    reply_markup=keyboard,
                    menu_type='delete_parts'
                )
            else:
                await self.send_and_store(
                    chat_id,
                    "⚠️ لا توجد أجزاء تحتوي على أسئلة للحذف",
                    menu_type='info'
                )
        
        except Exception as e:
            print(f"Error in show_parts_for_deletion: {e}")
            await self.show_delete_menu(chat_id)

    async def run(self):
        """تشغيل البوت"""
        print("✨ بدء تشغيل البوت")
        retry_count = 0
        while True:
            try:
                print("🔄 محاولة الاتصال بخوادم تيليجرام...")
                await self.bot.polling(non_stop=True, timeout=60)
                retry_count = 0
            except Exception as e:
                retry_count += 1
                wait_time = min(30, retry_count * 5)
                print(f"❌ خطأ في الاتصال: {e}")
                print(f"⏳ انتظار {wait_time} ثوانٍ قبل إعادة المحاولة...")
                await asyncio.sleep(wait_time)
                print("🔄 إعادة تشغيل البوت...")

if __name__ == "__main__":
    bot = Bot()
    asyncio.run(bot.run())