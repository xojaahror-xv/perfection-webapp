import asyncio
import logging
import html
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode

# BU YERGA O'Z BOTINGIZ TOKENINI QO'YING (BotFather dan olinadi)
BOT_TOKEN = "8713957586:AAGmtvnbrJpkiwy9IuvR2gF0bHwn8OBFGXY"

# BU YERGA WEB APP SULKASINI QO'YING (HTTPS bo'lishi shart)
WEB_APP_URL = "https://xojaahror-xv.github.io/perfection-webapp/" 

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    # Safe HTML-escaped name
    escaped_name = html.escape(message.from_user.full_name or "Foydalanuvchi")
    
    welcome_text = (
        f"Assalomu alaykum, <b>{escaped_name}</b>! 👋\n\n"
        f"🏫 <b>Perfection English School</b> rasmiy botiga xush kelibsiz!\n\n"
        f"🚀 Bizning yangi, zamonaviy va interaktiv ta'lim platformamizdan foydalanish uchun "
        f"pastdagi tugmani bosing va <b>Web Ilovamizga</b> kiring."
    )
    
    # Web App tugmasini yaratish
    web_app_btn = InlineKeyboardButton(
        text="📱 Ilovani Ochish", 
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    
    # Qo'shimcha tugmalar (zamonaviy ko'rinish uchun)
    help_btn = InlineKeyboardButton(text="💬 Yordam", callback_data="help")
    channel_btn = InlineKeyboardButton(text="📢 Kanalimiz", url="https://t.me/perfection_school")
    
    # Tugmalarni joylashtirish (1-qatorda Web App, 2-qatorda qolganlar)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [web_app_btn],
        [help_btn, channel_btn]
    ])

    # Rasm bilan birga yuborish (JPG formatida)
    photo_url = "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&auto=format&fit=crop&q=80"
    
    try:
        await message.answer_photo(
            photo=photo_url,
            caption=welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Failed to send photo: {e}")
        # Agar rasm yuklanmasa, oddiy matn yuborish
        await message.answer(
            welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

@dp.callback_query(lambda c: c.data == "help")
async def help_callback_handler(callback_query: types.CallbackQuery):
    help_text = (
        "❓ <b>Yordam bo'limi</b>\n\n"
        "Platformamizdan foydalanishda muammolar yuzaga kelsa yoki savollaringiz bo'lsa, "
        "quyidagi ma'muriyat bilan bog'lanishingiz mumkin:\n\n"
        "📞 Telefon: +998 90 123 45 67\n"
        "💬 Telegram: @perfection_admin\n\n"
        "Tizimga kirish uchun pastdagi '📱 Ilovani Ochish' tugmasini bosing."
    )
    try:
        await callback_query.answer()
        await callback_query.message.answer(help_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Callback query handler error: {e}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    print("Bot ishga tushdi... (Web App tugmasi tayyor)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

