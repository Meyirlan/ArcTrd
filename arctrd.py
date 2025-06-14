import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)

# Logging sozlamalari (xatoliklarni ko'rish uchun)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- BOT SOZLAMALARI (SHU YERNI O'ZGARTIRING) ---
BOT_TOKEN = "7615833495:AAH3m7h-adQunCkmjHv0pTMUYQsh2tz679I"  # @BotFather dan olingan token
ADMIN_ID = 6420024593  # @userinfobot dan olingan o'zingizning ID raqamingiz
GROUP_LINK = "https://t.me/+PR1WkbZkl6c3ZWRi"  # Yopiq kanalingiz uchun taklifnoma havolasi

# SIZNING TALABINGIZ ASOSIDA YANGILANGAN QISM
CARD_INFO = (
    "ArcTrd Family nomli yopiq guruhga oylik obuna uchun to'lov ma'lumotlari:\n\n"
    "💳 Karta raqami: 4073 4200 5285 6212\n"
    "💰 To'lov miqdori: 200,000 so'm\n"
    "⏳ Obuna muddati: 1 oy\n\n"
    "❗️ Iltimos, to'lovni amalga oshirib, kvitansiyani (chekni) rasm shaklida ushbu botga yuboring."
)
# ----------------------------------------------------

# ConversationHandler uchun holatlar
WAITING_CHECK = range(1)

# /start buyrug'i uchun funksiya
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("✅ Obuna bo'lish", callback_data="subscribe")],
        [InlineKeyboardButton("✍️ Adminga yozish", callback_data="contact_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Assalomu alaykum, ArcTrd Family botiga xush kelibsiz!\n\n"
        "Pullik kanalimizga qo'shilish uchun 'Obuna bo'lish' tugmasini bosing yoki savollaringiz bo'lsa 'Adminga yozish' tugmasidan foydalaning.",
        reply_markup=reply_markup,
    )

# Tugma bosishlarni boshqarish
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "subscribe":
        await query.edit_message_text(text=CARD_INFO)
        return WAITING_CHECK  # Chekni kutish holatiga o'tish
    elif query.data == "contact_admin":
        await query.edit_message_text(text="Savolingizni yoki murojaatingizni shu yerga yozing. Men uni adminga yetkazaman.")
        # Bu yerda suhbatni to'xtatish shart emas, chunki keyingi xabar forward_to_admin'ga tushadi
        return ConversationHandler.END

    # Admin uchun tasdiqlash/rad etish
    elif query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])
        try:
            # Kanalga qo'shilish uchun unikal havola yaratish (ixtiyoriy, lekin xavfsizroq)
            # Bu funksiya uchun bot kanalda admin bo'lishi va 'invite users' huquqiga ega bo'lishi kerak
            # invite_link = await context.bot.create_chat_invite_link(chat_id=GROUP_LINK, member_limit=1)
            # link_to_send = invite_link.invite_link
            link_to_send = GROUP_LINK # Yoki oddiy havola yuborish

            await context.bot.send_message(chat_id=user_id, text=f"🎉 Tabriklaymiz! To'lovingiz tasdiqlandi. Quyidagi havola orqali kanalga qo'shilishingiz mumkin:\n\n{link_to_send}")
            await query.edit_message_text(text=f"{user_id} uchun to'lov tasdiqlandi. Foydalanuvchiga havola yuborildi.")
        except Exception as e:
            await query.edit_message_text(text=f"Foydalanuvchiga xabar yuborishda xatolik: {e}")

    elif query.data.startswith("reject_"):
        user_id = int(query.data.split("_")[1])
        try:
            await context.bot.send_message(chat_id=user_id, text="😔 Afsuski, to'lovingiz tasdiqlanmadi. Iltimos, ma'lumotlarni tekshirib, qaytadan urinib ko'ring yoki admin bilan bog'laning.")
            await query.edit_message_text(text=f"{user_id} uchun to'lov rad etildi. Foydalanuvchiga xabar yuborildi.")
        except Exception as e:
            await query.edit_message_text(text=f"Foydalanuvchiga xabar yuborishda xatolik: {e}")

# Chekni qabul qilish funksiyasi
async def receive_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    photo = update.message.photo[-1] # Eng katta o'lchamdagi rasmni olish

    await update.message.reply_text("Rahmat! Chekingiz adminga yuborildi. Tasdiqlanishini kuting.")

    # Adminga chekni yuborish
    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user.id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption=f"Yangi to'lov!\n\nFoydalanuvchi: {user.full_name}\nUsername: @{user.username}\nID: {user.id}",
        reply_markup=reply_markup,
    )
    return ConversationHandler.END # Suhbatni yakunlash

# Adminga murojaatni yuborish va javobni qaytarish
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user

    # Agar admin o'ziga o'zi yozsa yoki javob qaytarayotgan bo'lsa
    if user.id == ADMIN_ID:
        # Admin javob qaytarayotganini tekshirish
        if update.message.reply_to_message and update.message.reply_to_message.forward_from:
            original_user_id = update.message.reply_to_message.forward_from.id
            try:
                await context.bot.send_message(chat_id=original_user_id, text=f"Admin javobi:\n\n{update.message.text}")
                await update.message.reply_text("✅ Javobingiz foydalanuvchiga yuborildi.")
            except Exception as e:
                await update.message.reply_text(f"❌ Foydalanuvchiga javob yuborishda xatolik: {e}")
        return

    # Oddiy foydalanuvchidan kelgan xabarni adminga yuborish
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=user.id,
        message_id=update.message.message_id
    )
    await update.message.reply_text("✍️ Xabaringiz adminga yuborildi. Tez orada javob berishadi.")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Obuna bo'lish suhbati
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="^subscribe$")],
        states={
            WAITING_CHECK: [MessageHandler(filters.PHOTO, receive_check)],
        },
        fallbacks=[CommandHandler('start', start)],
        conversation_timeout=600 # Foydalanuvchi 10 daqiqa chek yubormasa, suhbat tugaydi
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button)) # Boshqa barcha tugmalar uchun
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin)) # Matnli xabarlar uchun

    application.run_polling()

if __name__ == "__main__":
    main()
