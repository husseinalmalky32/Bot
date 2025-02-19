import asyncio
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# تكوين السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# رمز البوت
TOKEN = '7873463536:AAEqLMQLEmJVKGO8ebaBgcw9kxP6yE9SUO0'  # قم بتغيير هذا برمز البوت الخاص بك

# تعريف حالات المحادثة
CHOOSING = 1

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر البدء مع أزرار الاختيار"""
    welcome_message = """
🌟 مرحباً بك في بوت الاختبارات! 🌟

اختر طريقة إدخال السؤال:
"""
    keyboard = [
        [
            InlineKeyboardButton("📝 كتابة سؤال", callback_data='write_question'),
            InlineKeyboardButton("📁 إرسال ملف", callback_data='send_file')
        ],
        [InlineKeyboardButton("❓ مساعدة", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return CHOOSING

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()

    if query.data == 'write_question':
        instructions = """
📝 لكتابة سؤال، اتبع التنسيق التالي:

السؤال
✓ الإجابة الصحيحة
✗ إجابة خاطئة
✗ إجابة خاطئة
✗ إجابة خاطئة

✨ مثال:
ما هي عاصمة السعودية؟
✓ الرياض
✗ جدة
✗ مكة
✗ الدمام

🚀 اكتب سؤالك الآن!
"""
        await query.message.edit_text(instructions)

    elif query.data == 'send_file':
        instructions = """
📁 لإرسال ملف أسئلة:

1️⃣ جهز ملف نصي يحتوي على الأسئلة
2️⃣ اكتب كل سؤال بالتنسيق التالي:

السؤال
✓ الإجابة الصحيحة
✗ إجابة خاطئة
✗ إجابة خاطئة
✗ إجابة خاطئة

3️⃣ اترك سطر فارغ بين كل سؤال وآخر
4️⃣ أرسل الملف الآن!
"""
        await query.message.edit_text(instructions)

    elif query.data == 'help':
        help_message = """
❓ مساعدة في استخدام البوت:

1️⃣ كتابة سؤال:
• اكتب السؤال في رسالة واحدة
• استخدم ✓ للإجابة الصحيحة
• استخدم ✗ للإجابات الخاطئة

2️⃣ إرسال ملف:
• يمكن إرسال ملف يحتوي على عدة أسئلة
• اترك سطر فارغ بين الأسئلة

📌 للعودة للقائمة الرئيسية اكتب /start
"""
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(help_message, reply_markup=reply_markup)

    elif query.data == 'back_to_main':
        await start_command(update, context)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    try:
        message_text = update.message.text
        lines = [line.strip() for line in message_text.split('\n') if line.strip()]
        
        if len(lines) < 3:
            await update.message.reply_text("""
❌ تنسيق غير صحيح. الرجاء استخدام التنسيق التالي:

السؤال
✓ الإجابة الصحيحة
✗ إجابة خاطئة
✗ إجابة خاطئة
✗ إجابة خاطئة""")
            return
        
        question = lines[0]
        options = []
        correct_option = None
        
        for line in lines[1:]:
            if '✓' in line or '✗' in line:
                option = line.replace('✓', '').replace('✗', '').strip('- ').strip()
                if '✓' in line:
                    correct_option = option
                options.append(option)
            else:
                options.append(line.strip('- ').strip())
        
        if not correct_option and options:
            correct_option = options[0]
        
        if len(options) < 2:
            await update.message.reply_text("❌ يجب توفير خيارين على الأقل!")
            return
        
        random.shuffle(options)
        correct_option_id = options.index(correct_option)
        
        await context.bot.send_poll(
            chat_id=update.message.chat_id,
            question=question,
            options=options,
            type='quiz',
            correct_option_id=correct_option_id,
            is_anonymous=False,
            explanation=f"💡 الإجابة الصحيحة هي: {correct_option}"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_text_message: {str(e)}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الملفات"""
    try:
        if not update.message.document:
            await update.message.reply_text("❌ الرجاء إرسال ملف")
            return
        
        file = await update.message.document.get_file()
        file_name = update.message.document.file_name
        await file.download_to_drive('received_file')
        
        try:
            with open('received_file', 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except UnicodeDecodeError:
            try:
                with open('received_file', 'r', encoding='windows-1256') as f:
                    content = f.read().strip()
            except:
                await update.message.reply_text("❌ لم نتمكن من قراءة الملف")
                return
        
        questions = [q.strip() for q in content.split('\n\n') if q.strip()]
        
        if not questions:
            await update.message.reply_text("❌ لم يتم العثور على أسئلة في الملف")
            return
        
        await update.message.reply_text(f"📚 تم استلام {len(questions)} سؤال")
        
        for index, question_text in enumerate(questions, 1):
            try:
                lines = [line.strip() for line in question_text.split('\n') if line.strip()]
                
                if len(lines) < 2:
                    continue
                    
                question = lines[0]
                options = []
                correct_option = None
                
                for line in lines[1:]:
                    if '✓' in line or '✗' in line:
                        option = line.replace('✓', '').replace('✗', '').strip('- ').strip()
                        if '✓' in line:
                            correct_option = option
                        options.append(option)
                    else:
                        options.append(line.strip('- ').strip())
                
                if not correct_option and options:
                    correct_option = options[0]
                
                random.shuffle(options)
                correct_option_id = options.index(correct_option)
                
                await context.bot.send_poll(
                    chat_id=update.message.chat_id,
                    question=f"السؤال {index}: {question}",
                    options=options,
                    type='quiz',
                    correct_option_id=correct_option_id,
                    is_anonymous=False,
                    explanation=f"💡 الإجابة الصحيحة هي: {correct_option}"
                )
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in question {index}: {str(e)}")
                await update.message.reply_text(f"❌ خطأ في السؤال {index}: {str(e)}")
        
        await update.message.reply_text("✅ تم إرسال جميع الأسئلة بنجاح!")
        
    except Exception as e:
        logger.error(f"Error in handle_document: {str(e)}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

def main():
    """تشغيل البوت"""
    try:
        # إنشاء التطبيق
        application = ApplicationBuilder().token(TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler('start', start_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        
        # بدء تشغيل البوت
        print("🤖 البوت يعمل الآن...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")

if __name__ == '__main__':
    main()
