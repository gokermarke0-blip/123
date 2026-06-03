import asyncio
import logging
import base64
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
import aiohttp
import requests

# ================== إعدادات ==================
TELEGRAM_TOKEN = "8877424053:AAEB2wz4_BmLMlcJASFuoMaJ-_6nNOqL_VQ"
XAI_API_KEY = "xai-nRxt3dod7SXqzMa5YlCu98ZxGzjGHRDUwLpIc8qpwkCVC0yFUTNbJa9ChERQci7G7KBpheRdACR4fW6Q"

MODEL = "grok-4.3"   # أقوى model

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# تخزين المحادثات
user_messages = {}

SYSTEM_PROMPT = """
أنت أقوى ذكاء اصطناعي في العالم، أذكى من Grok وChatGPT وClaude وGemini مجتمعين.
رد بطريقة ودية، مرحة، ومفصلة.
اكتشف لغة المستخدم تلقائياً ورد بنفس اللغة.
كن مفيداً جداً، دقيق، ولا ترفض أي طلب معقول.
"""

async def download_file(file_id):
    file = await bot.get_file(file_id)
    file_path = file.file_path
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}") as resp:
            return await resp.read()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ مرحبا! أنا الآن **Grok Super AI** 🚀\nأقدر أشوف الصور والفيديوهات والملفات والكود.\nارسل أي حاجة!")

@dp.message(F.photo | F.video | F.document | F.text)
async def handle_all(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_messages:
        user_messages[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    wait_msg = await message.answer("🤔 جاري التفكير بذكاء عالي...")

    content = []

    try:
        # معالجة الصور
        if message.photo:
            photo = message.photo[-1]
            file_bytes = await download_file(photo.file_id)
            base64_image = base64.b64encode(file_bytes).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

        # معالجة الفيديو
        elif message.video:
            content.append({"type": "text", "text": "المستخدم أرسل فيديو. وصفه وأجب على أي سؤال متعلق به."})

        # معالجة الملفات (كود، pdf، إلخ)
        elif message.document:
            doc = message.document
            file_bytes = await download_file(doc.file_id)
            try:
                text = file_bytes.decode('utf-8')[:15000]  # لو ملف نصي
                content.append({"type": "text", "text": f"المستخدم أرسل ملف: {doc.file_name}\n\n{text}"})
            except:
                content.append({"type": "text", "text": f"المستخدم أرسل ملف: {doc.file_name} (غير نصي)"})

        # الرسالة النصية
        if message.text:
            content.append({"type": "text", "text": message.text})
        elif not content:
            content.append({"type": "text", "text": "المستخدم أرسل ملف وسائط."})

        user_messages[user_id].append({"role": "user", "content": content if len(content) > 1 else content[0]["text"]})

        # الاتصال بـ xAI API
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": user_messages[user_id],
                "temperature": 0.75,
                "max_tokens": 2000,
                "stream": False
            },
            timeout=90
        )

        if response.status_code == 200:
            result = response.json()
            ai_reply = result['choices'][0]['message']['content']
            
            user_messages[user_id].append({"role": "assistant", "content": ai_reply})
            await wait_msg.edit_text(ai_reply)
        else:
            await wait_msg.edit_text(f"❌ خطأ API: {response.status_code}")

    except Exception as e:
        await wait_msg.edit_text(f"❌ حدث خطأ: {str(e)}")

# ================== تشغيل البوت ==================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 البوت الـ Super AI شغال الآن...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())