import telebot
from telebot import types
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from googletrans import Translator
import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import io
import os
import time
import ssl
import logging
from datetime import datetime
from pathlib import Path

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تكوين البوت
BOT_TOKEN = '7748208067:AAEJ3urMl0dPS9Y3jVEkoIXsw8dKeshaXds'
bot = telebot.TeleBot(BOT_TOKEN)

# الرموز التعبيرية
EMOJIS = {
    'welcome': '👋',
    'book': '📚',
    'success': '✅',
    'error': '❌',
    'loading': '⏳',
    'search': '🔍',
    'stats': '📊',
    'learn': '🎓',
    'settings': '⚙️',
    'dictionary': '📖',
    'translate': '🔄',
    'page': '📄',
    'done': '✨'
}

class FontManager:
    FONTS = {
        'Amiri': {
            'url': 'https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf',
            'filename': 'Amiri-Regular.ttf'
        },
        'Cairo': {
            'url': 'https://github.com/google/fonts/raw/main/ofl/cairo/Cairo-Regular.ttf',
            'filename': 'Cairo-Regular.ttf'
        }
    }

    def __init__(self):
        self.fonts_dir = Path('fonts')
        self.current_font = None
        self.setup_fonts_directory()

    def setup_fonts_directory(self):
        """إنشاء مجلد الخطوط"""
        if not self.fonts_dir.exists():
            self.fonts_dir.mkdir(parents=True, exist_ok=True)

    def download_font(self, font_name):
        """تحميل الخط"""
        try:
            font_info = self.FONTS.get(font_name)
            if not font_info:
                return None

            font_path = self.fonts_dir / font_info['filename']
            if font_path.exists():
                return font_path

            response = requests.get(font_info['url'], timeout=10)
            response.raise_for_status()

            with open(font_path, 'wb') as f:
                f.write(response.content)

            return font_path

        except Exception as e:
            logger.error(f"Font download error: {str(e)}")
            return None

    def initialize_font(self):
        """تهيئة الخط العربي"""
        for font_name in self.FONTS:
            try:
                font_path = self.download_font(font_name)
                if font_path and font_path.exists():
                    pdfmetrics.registerFont(TTFont('Arabic', str(font_path)))
                    self.current_font = 'Arabic'
                    return True
            except Exception as e:
                logger.error(f"Font initialization error: {str(e)}")
                continue
        return False

class TechnicalTranslator:
    def __init__(self, dictionary_path='technical_dictionary.json'):
        self.dictionary_path = dictionary_path
        self.translator = Translator()
        self.technical_terms = {}
        self.translation_memory = {}
        self.load_dictionary()

    def load_dictionary(self):
        """تحميل القاموس التقني"""
        try:
            if os.path.exists(self.dictionary_path):
                with open(self.dictionary_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    for category in data.values():
                        self.technical_terms.update(category)
        except Exception as e:
            logger.error(f"Dictionary loading error: {str(e)}")
            self.technical_terms = {}

    def translate_text(self, text):
        """ترجمة النص مع مراعاة المصطلحات التقنية"""
        try:
            if not text.strip():
                return ""

            # تقسيم النص إلى جمل
            sentences = text.split('.')
            translated_sentences = []

            for sentence in sentences:
                if not sentence.strip():
                    continue

                # البحث عن المصطلحات التقنية
                words = sentence.split()
                translated_words = []

                for word in words:
                    # تجاهل الأرقام والرموز
                    if not any(c.isalpha() for c in word):
                        translated_words.append(word)
                        continue

                    # البحث في الذاكرة
                    if word in self.translation_memory:
                        translated_words.append(self.translation_memory[word])
                        continue

                    # البحث في القاموس
                    technical_translation = self.find_technical_term(word)
                    if technical_translation:
                        translated_words.append(technical_translation)
                        self.translation_memory[word] = technical_translation
                        continue

                    # الترجمة العامة
                    try:
                        translation = self.translator.translate(word, dest='ar')
                        translated_words.append(translation.text)
                        self.translation_memory[word] = translation.text
                    except:
                        translated_words.append(word)

                translated_sentences.append(' '.join(translated_words))

            return '. '.join(translated_sentences)

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text

    def find_technical_term(self, word):
        """البحث عن المصطلح في القاموس"""
        word_variations = [
            word,
            word.lower(),
            word.upper(),
            word.capitalize(),
            word.title()
        ]
        
        for variation in word_variations:
            if variation in self.technical_terms:
                return self.technical_terms[variation]
        return None

# تهيئة المدير الخطوط
font_manager = FontManager()
def create_beautiful_message(title, content, style='default'):
    """إنشاء رسائل منسقة"""
    if style == 'progress':
        message = f"""
╭─〘 {title} 〙
│ {content}
╰─⌛ جاري المعالجة..."""
    elif style == 'success':
        message = f"""
╭─〘 {title} 〙
│ {content}
╰─{EMOJIS['success']} تمت العملية بنجاح!"""
    elif style == 'error':
        message = f"""
╭─〘 {title} 〙
│ {content}
╰─{EMOJIS['error']} حدث خطأ!"""
    else:
        message = f"""
╭─〘 {title} 〙
│ {content}
╰────────"""
    return message

def create_pdf_with_arabic(packet, text, page_width=595, page_height=842):
    """إنشاء PDF مع دعم اللغة العربية"""
    try:
        c = canvas.Canvas(packet)
        
        # استخدام الخط العربي إذا كان متوفراً
        if font_manager.current_font:
            c.setFont(font_manager.current_font, 12)
        else:
            c.setFont("Helvetica", 12)

        y = page_height - 50
        margin = 50
        width = page_width - (2 * margin)

        lines = text.split('\n')
        for line in lines:
            if line.strip():
                # تقسيم السطور الطويلة
                wrapped_lines = simpleSplit(
                    line,
                    font_manager.current_font or "Helvetica",
                    12,
                    width
                )
                for wrapped_line in wrapped_lines:
                    # كتابة النص من اليمين إلى اليسار
                    text_width = c.stringWidth(
                        wrapped_line,
                        font_manager.current_font or "Helvetica",
                        12
                    )
                    c.drawString(
                        page_width - margin - text_width,
                        y,
                        wrapped_line
                    )
                    y -= 20
            else:
                y -= 20

            if y < 50:
                c.showPage()
                if font_manager.current_font:
                    c.setFont(font_manager.current_font, 12)
                else:
                    c.setFont("Helvetica", 12)
                y = page_height - 50

        c.save()
        return packet
    except Exception as e:
        logger.error(f"PDF creation error: {str(e)}")
        raise

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """معالجة أمر البدء"""
    welcome_text = create_beautiful_message(
        f"مرحباً {EMOJIS['welcome']}",
        f"""
{EMOJIS['book']} مرحباً بك في بوت الترجمة التقني المتخصص

• ترجمة دقيقة للمستندات التقنية
• دعم للمصطلحات المتخصصة
• ترجمة ذكية ومتطورة

{EMOJIS['translate']} أرسل ملف PDF للبدء"""
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("المساعدة 💡", callback_data="help"),
        types.InlineKeyboardButton("حول البوت ℹ️", callback_data="about")
    )
    bot.reply_to(message, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة الأزرار التفاعلية"""
    try:
        if call.data == "help":
            help_text = create_beautiful_message(
                f"المساعدة {EMOJIS['book']}",
                """
• أرسل ملف PDF للترجمة
• حجم الملف الأقصى: 20MB
• يدعم النصوص التقنية والعلمية
• ترجمة فورية ودقيقة"""
            )
            bot.edit_message_text(
                help_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=call.message.reply_markup
            )
        elif call.data == "about":
            about_text = create_beautiful_message(
                "حول البوت ℹ️",
                """
• بوت ترجمة تقني متخصص
• يستخدم قاموساً تقنياً شاملاً
• تحديثات مستمرة للمصطلحات
• دعم فني متواصل"""
            )
            bot.edit_message_text(
                about_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=call.message.reply_markup
            )
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    """معالجة الملفات المرسلة"""
    try:
        if not message.document.file_name.lower().endswith('.pdf'):
            error_msg = create_beautiful_message(
                f"خطأ في الملف {EMOJIS['error']}",
                "الرجاء إرسال ملف PDF فقط!",
                style='error'
            )
            bot.reply_to(message, error_msg)
            return

        if message.document.file_size > 20000000:  # 20MB
            error_msg = create_beautiful_message(
                f"خطأ في حجم الملف {EMOJIS['error']}",
                "حجم الملف يتجاوز 20 ميجابايت!",
                style='error'
            )
            bot.reply_to(message, error_msg)
            return

        # بدء العملية
        status_message = bot.reply_to(
            message,
            create_beautiful_message(
                f"جارٍ المعالجة {EMOJIS['loading']}",
                "جارٍ تحميل الملف...",
                style='progress'
            )
        )

        # تحميل الملف
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # إنشاء الملفات المؤقتة
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = f"temp_input_{timestamp}.pdf"
        output_path = f"temp_output_{timestamp}.pdf"

        with open(input_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # ترجمة الملف
        translator = TechnicalTranslator()
        reader = PdfReader(input_path)
        writer = PdfWriter()

        total_pages = len(reader.pages)
        for i, page in enumerate(reader.pages, 1):
            try:
                # تحديث حالة التقدم
                bot.edit_message_text(
                    create_beautiful_message(
                        f"جارٍ الترجمة {EMOJIS['translate']}",
                        f"جارٍ ترجمة الصفحة {i} من {total_pages}",
                        style='progress'
                    ),
                    status_message.chat.id,
                    status_message.message_id
                )

                # معالجة الصفحة
                text = page.extract_text()
                translated_text = translator.translate_text(text)
                
                # إنشاء PDF جديد
                packet = io.BytesIO()
                packet = create_pdf_with_arabic(
                    packet,
                    translated_text,
                    page.mediabox.width,
                    page.mediabox.height
                )
                packet.seek(0)

                # دمج الصفحات
                new_page = PdfReader(packet).pages[0]
                page.merge_page(new_page)
                writer.add_page(page)

            except Exception as e:
                logger.error(f"Page processing error: {str(e)}")
                writer.add_page(page)

        # حفظ الملف النهائي
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        # إرسال الملف المترجم
        with open(output_path, 'rb') as doc:
            bot.send_document(
                message.chat.id,
                doc,
                caption=create_beautiful_message(
                    f"اكتملت الترجمة {EMOJIS['done']}",
                    f"""• عدد الصفحات: {total_pages}
• تمت المعالجة بنجاح
• تم حفظ المصطلحات التقنية""",
                    style='success'
                )
            )

        # تنظيف الملفات المؤقتة
        os.remove(input_path)
        os.remove(output_path)

    except Exception as e:
        logger.error(f"Document handling error: {str(e)}")
        error_message = create_beautiful_message(
            f"خطأ {EMOJIS['error']}",
            f"حدث خطأ: {str(e)}",
            style='error'
        )
        bot.reply_to(message, error_message)

def main():
    """الدالة الرئيسية"""
    print(create_beautiful_message(
        "تشغيل البوت 🚀",
        "جارٍ بدء تشغيل البوت..."
    ))
    
    # تهيئة الخطوط
    if not font_manager.initialize_font():
        logger.warning("Failed to initialize Arabic fonts")

    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    main()