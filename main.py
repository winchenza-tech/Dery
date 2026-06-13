import os
import PIL.Image
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
        # Kodun hicbir yerinde yildiz sembolu kalmamasini garanti eder
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

    user_text = ""
    photo = None

    # 1. Durum: Kullanici dogrudan fotograf yukleyip altina aciklama yazdiysa
    if update.message.photo:
        photo = update.message.photo[-1]
        if update.message.caption:
            parts = update.message.caption.split(maxsplit=1)
            user_text = parts[1] if len(parts) > 1 else ""
    
    # 2. Durum: Kullanici bir mesaja (gorsel veya metin) /sor diyerek yanit verdiyle
    elif update.message.reply_to_message:
        if update.message.reply_to_message.photo:
            photo = update.message.reply_to_message.photo[-1]
        elif update.message.reply_to_message.text:
            user_text = update.message.reply_to_message.text
        
        # Yanit verirken yanina ek bir soru eklediyse onu da yakalayalim
        if update.message.text:
            parts = update.message.text.split(maxsplit=1)
            if len(parts) > 1:
                user_text = f"{user_text} {parts[1]}".strip()

    # 3. Durum: Kullanici gorselsiz, sadece metin olarak /sor soru yazdiysa
    else:
        if update.message.text:
            parts = update.message.text.split(maxsplit=1)
            user_text = parts[1] if len(parts) > 1 else ""

    # Eger hicbir veri (gorsel veya metin) yakalanamadiysa uyaralim
    if not photo and not user_text:
        await update.message.reply_text("bir soru yaz veya bir görsel ekle 📝📸")
        return

    # Gemini'ye gonderilecek icerik listesi
    girdi_icerigi = []
    
    # Eger gorsel varsa listeye ekle
    if photo:
        dosya = await context.bot.get_file(photo.file_id)
        dosya_yolu = "gecici_gorsel.jpg"
        await dosya.download_to_drive(dosya_yolu)
        img = PIL.Image.open(dosya_yolu)
        girdi_icerigi.append(img)

    # Yapay zekaya verilecek talimatlar
    prompt = f"Sen samimi bir asistansın. Soruyu soran kişi: {kisi}. {hitap_kurali} "
    if user_text:
        prompt += f"Kullanıcının sorusu veya mesajı şu şekildedir: '{user_text}'. "
    if photo:
        prompt += "Görseldeki durumu, soruyu veya detayları da analiz et. "
    
    prompt += "Soruyu samimi bir dille yanıtla. Maksimum 200 kelime kullan, cevap kısaysa uzatma. Asla yıldız sembolü kullanma. Mesajlarında uygun emojiler kullanabilirsin."
    
    girdi_icerigi.append(prompt)

    # Gemini'den yanit al (Sadece metin veya gorsel+metin multimedya otomatik ayarlanir)
    response = model.generate_content(girdi_icerigi)
    temiz_cevap = metni_temizle(response.text)
    
    await update.message.reply_text(temiz_cevap)

async def berat_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kullanici_adi = update.effective_user.username
    
    if kullanici_adi and kullanici_adi.lower() == 'zenithar':
        await update.message.reply_text("Ben Berat, yalnızca Derya’ya yavşarım. 😎")
        return

    prompt = "Senin adın Berat. Karşındaki kişi Derya. Derya'ya çok zekice, ince esprili ve muzip bir şekilde flörtöz sözler söyle (yavşa). Maksimum 50-60 kelime olsun. Asla yıldız sembolü kullanma. Bolca uygun emoji kullanabilirsin."
    
    response = model.generate_content(prompt)
    temiz_cevap = metni_temizle(response.text)
    
    await update.message.reply_text(temiz_cevap)

def main():
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        print("HATA: TELEGRAM_BOT_TOKEN veya GEMINI_API_KEY eksik!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("sor", sor_komutu))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r'^/sor'), sor_komutu))
    app.add_handler(CommandHandler("beratol", berat_komutu))

    print("Bot aktif, komutlar bekleniyor...")
    app.run_polling()

if __name__ == '__main__':
    main()
