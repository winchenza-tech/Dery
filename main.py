import os
import PIL.Image
import datetime
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Railway ortam degiskenleri
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def metni_temizle(metin):
    if metin:
        return metin.replace(chr(42), '')
    return ""

async def sor_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kullanici_adi = update.effective_user.username
    if kullanici_adi and kullanici_adi.lower() == 'zenithar':
        kisi = "zenithar"
        hitap_kurali = ""
    else:
        kisi = "Derya"
        hitap_kurali = "Soran kişi Derya olduğu için ona kesinlikle 'Deryacığım' diye hitap et."

    photo = None
    if update.message.photo:
        photo = update.message.photo[-1]
    elif update.message.reply_to_message and update.message.reply_to_message.photo:
        photo = update.message.reply_to_message.photo[-1]

    if not photo:
        await update.message.reply_text("Lütfen bir görselle birlikte /sor yazın veya bir görsele /sor diyerek yanıt verin 📸")
        return

    dosya = await context.bot.get_file(photo.file_id)
    dosya_yolu = "gecici_gorsel.jpg"
    await dosya.download_to_drive(dosya_yolu)
    img = PIL.Image.open(dosya_yolu)

    prompt = f"Sen samimi bir asistansın. Soruyu soran kişi: {kisi}. {hitap_kurali} Görseldeki soruyu veya durumu anla ve samimi bir dille yanıtla. Maksimum 200 kelime kullan, cevap kısaysa uzatma. Asla o yasaklı karakteri kullanma. Emoji kullanabilirsin."

    response = model.generate_content([prompt, img])
    temiz_cevap = metni_temizle(response.text)
    
    await update.message.reply_text(temiz_cevap)

async def berat_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kullanici_adi = update.effective_user.username
    
    if kullanici_adi and kullanici_adi.lower() == 'zenithar':
        await update.message.reply_text("Ben Berat, yalnızca Derya’ya yavşarım. 😎")
        return

    prompt = "Senin adın Berat. Karşındaki kişi Derya. Derya'ya çok zekice, ince esprili ve muzip bir şekilde flörtöz sözler söyle (yavşa). Maksimum 50-60 kelime olsun. Asla o yasaklı karakteri kullanma. Bolca uygun emoji kullanabilirsin."
    
    response = model.generate_content(prompt)
    temiz_cevap = metni_temizle(response.text)
    
    await update.message.reply_text(temiz_cevap)

async def gunluk_iliski_sorusu(context: ContextTypes.DEFAULT_TYPE):
    # Gorev tetiklendiginde botun bulundugu aktif sohbet alanina mesaji gonderir
    job = context.job
    prompt = "Berat ve Derya'ya yönelik, ikisinin yanıtlaması için zorlu ve derin bir ilişki sorusu hazırla. Şartlar: Eski sevgililerle ilgili OLMASIN. Düşündürücü ve eğlenceli olsun. Asla o yasaklı karakteri kullanma. Emoji kullanabilirsin."
    
    response = model.generate_content(prompt)
    temiz_cevap = metni_temizle(response.text)
    
    await context.bot.send_message(chat_id=job.chat_id, text=temiz_cevap)

def main():
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        print("HATA: TELEGRAM_BOT_TOKEN veya GEMINI_API_KEY bulunamadı!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("sor", sor_komutu))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r'^/sor'), sor_komutu))
    app.add_handler(CommandHandler("beratcayavsa", berat_komutu))

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == '__main__':
    main()
