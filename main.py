import os
import PIL.Image
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Railway ortam degiskenleri
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
# Gemini 2.5 Flash modeli tanimlandi
model = genai.GenerativeModel('gemini-2.5-flash')

def metni_temizle(metin):
    if metin:
        # Kodun ve yapay zekanin hicbir yerinde yildiz sembolu kalmamasini garanti eder
        return metin.replace(chr(42), '')
    return ""

async def sor_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kullanici_adi = user.username
    ad = user.first_name
    
    # Zenithar Kontrolü
    is_zenithar = False
    if kullanici_adi and kullanici_adi.lower() == 'zenithar':
        is_zenithar = True
    elif ad and 'zenithar' in ad.lower():
        is_zenithar = True

    if is_zenithar:
        kisi = "zenithar"
        hitap_kurali = ""
    else:
        kisi = "Derya"
        hitap_kurali = "Soran kişi Derya olduğu için ona kesinlikle 'Deryacığım' diye hitap et."

    user_text = ""
    photo = None

    if update.message.photo:
        photo = update.message.photo[-1]
        if update.message.caption:
            parts = update.message.caption.split(maxsplit=1)
            user_text = parts[1] if len(parts) > 1 else ""
    
    elif update.message.reply_to_message:
        if update.message.reply_to_message.photo:
            photo = update.message.reply_to_message.photo[-1]
        
        if update.message.reply_to_message.text:
            user_text = update.message.reply_to_message.text
        elif update.message.reply_to_message.caption:
            user_text = update.message.reply_to_message.caption
        
        if update.message.text:
            parts = update.message.text.split(maxsplit=1)
            if len(parts) > 1:
                user_text = f"{user_text} {parts[1]}".strip()

    else:
        if update.message.text:
            parts = update.message.text.split(maxsplit=1)
            user_text = parts[1] if len(parts) > 1 else ""

    if not photo and not user_text:
        await update.message.reply_text("Lütfen bir soru yazın veya bir görsel ekleyin 📝📸")
        return

    try:
        # Isteginize gore durum mesaji guncellendi
        bilgi_mesaji = await update.message.reply_text("Berat gibi düşünüyorum... 🤔⏳")

        girdi_icerigi = []
        if photo:
            dosya = await context.bot.get_file(photo.file_id)
            dosya_yolu = "gecici_gorsel.jpg"
            await dosya.download_to_drive(dosya_yolu)
            img = PIL.Image.open(dosya_yolu)
            girdi_icerigi.append(img)

        prompt = f"Sen samimi bir asistansın. Soruyu sabırla ve içtenlikle yanıtla. Soruyu soran kişi: {kisi}. {hitap_kurali} "
        if user_text:
            prompt += f"Kullanıcının sorusu veya mesajı şu şekildedir: '{user_text}'. "
        if photo:
            prompt += "Görseldeki durumu, soruyu veya detayları da analiz et. "
        
        prompt += "Soruyu samimi bir dille yanıtla. Maksimum 200 kelime kullan, cevap kısaysa uzatma. Asla yıldız sembolü kullanma. Mesajlarında uygun emojiler kullanabilirsin."
        
        girdi_icerigi.append(prompt)

        response = await model.generate_content_async(girdi_icerigi)
        temiz_cevap = metni_temizle(response.text)
        
        await bilgi_mesaji.delete()
        await update.message.reply_text(temiz_cevap)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Gemini API Hatası:\n`{str(e)[:500]}`", parse_mode='Markdown')


async def berat_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kullanici_adi = user.username
    ad = user.first_name
    
    is_zenithar = False
    if kullanici_adi and kullanici_adi.lower() == 'zenithar':
        is_zenithar = True
    elif ad and 'zenithar' in ad.lower():
        is_zenithar = True

    if is_zenithar:
        await update.message.reply_text("Ben Berat, yalnızca Derya’ya yavşarım. 😎")
        return

    try:
        # Isteginize gore durum mesaji guncellendi
        bilgi_mesaji = await update.message.reply_text("Berat oluyorum... 😎⏳")
        
        # Alintilanan mesaj kontrolü
        alinti_metni = ""
        if update.message.reply_to_message:
            if update.message.reply_to_message.text:
                alinti_metni = update.message.reply_to_message.text
            elif update.message.reply_to_message.caption:
                alinti_metni = update.message.reply_to_message.caption

        prompt = "Senin adın Berat. Karşındaki kişi Derya. Derya'ya çok zekice, ince esprili ve muzip bir şekilde flörtöz sözler söyle (yavşa). "
        
        # Eger bir mesaj alintilandiysa promptu ona gore ozellestiriyoruz
        if alinti_metni:
            prompt += f"Derya şu an şu mesajı yazdı veya bu mesaja yanıt veriyorsun: '{alinti_metni}'. Bu mesaja doğrudan ve çok zekice atıfta bulunarak, konuyu ince bir espriyle flörte bağla. "
        
        prompt += "Maksimum 50-60 kelime olsun. Asla yıldız sembolü kullanma. Bolca uygun emoji kullanabilirsin."
        
        response = await model.generate_content_async(prompt)
        temiz_cevap = metni_temizle(response.text)
        
        await bilgi_mesaji.delete()
        await update.message.reply_text(temiz_cevap)
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ Hata oluştu:\n`{str(e)[:500]}`", parse_mode='Markdown')

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
