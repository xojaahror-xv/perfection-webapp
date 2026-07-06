from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
from groq import Groq

app = FastAPI(title="Perfection English School API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WritingRequest(BaseModel):
    text: Optional[str] = ""
    task_type: str = "General" 
    image_data: Optional[str] = None
    prompt: Optional[str] = ""
    telegram_id: Optional[str] = None # Foydalanuvchini aniqlash uchun

class OnboardRequest(BaseModel):
    telegram_id: str
    full_name: str
    phone_number: str
    level: str


# Groq API ni sozlash
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

# ----------------- YANGI API LAR (Database va Gamification) -----------------

@app.post("/api/users/onboard")
async def onboard_user(req: OnboardRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.telegram_id == req.telegram_id).first()
    if user:
        # User already exists, update login/streak
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return {"status": "success", "message": "User logged in", "points": user.points}
    else:
        # Create new user
        new_user = models.User(
            telegram_id=req.telegram_id,
            full_name=req.full_name,
# -------------------------------------------------------------------------

@app.post("/api/check_writing")
async def check_writing(req: WritingRequest):
    if (not req.text or len(req.text.strip()) < 10) and not req.image_data:
        raise HTTPException(status_code=400, detail="Matn yoki rasm yuborilmadi.")
        
    if not client:
        return {
            "overall_band": "XATO",
            "grammar_feedback": "",
            "vocabulary_feedback": "",
            "coherence_feedback": "",
            "general_feedback": "DIQQAT: GROQ_API_KEY topilmadi! Renderda kalitni to'g'ri qo'yganingizni tekshiring."
        }
        
    prompt_clause = f"\n    Topshiriq mavzusi (Prompt):\n    \"\"\"{req.prompt}\"\"\"" if req.prompt else ""
    prompt = f"""
    Siz IELTS/CEFR examiner va malakali Ingliz tili o'qituvchisisiz. 
    Quyidagi o'quvchi yozgan inshoni tekshiring.
    Vazifa turi: {req.task_type}{prompt_clause}
    Matn:
    \"\"\"{req.text}\"\"\"
    
    Quyidagi JSON formatda javob qaytaring (hech qanday boshqa so'zlarsiz, faqat JSON formatda):
    {{
        "overall_band": "Masalan: 6.5 yoki B2",
        "grammar_feedback": "Grammatika bo'yicha xatolar va tahlil",
        "vocabulary_feedback": "So'z boyligi bo'yicha maslahatlar",
        "coherence_feedback": "Matn mantiqiyligi bo'yicha izoh",
        "general_feedback": "Umumiy xulosa"
    }}
    Barcha izohlaringiz o'zbek tilida yozilsin.
    """
    
    try:
        if req.image_data:
            # Agar rasm yuborilgan bo'lsa, maxsus Vision modelidan foydalanamiz
            model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": req.image_data
                            }
                        }
                    ]
                }
            ]
        else:
            # Faqat matn bo'lsa, eng aqlli va tezkor Llama 3.3 modelidan foydalanamiz
            model_name = "llama-3.3-70b-versatile"
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name,
            temperature=0.2
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Ortiqcha belgilarni tozalab, JSON ga aylantirish
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        result = json.loads(response_text)
        
        # O'quvchi xatosiz yozgan bo'lsa yoki yozish qismidan o'tsa +5 ball qo'shish
        # Agar telegram_id yuborilgan bo'lsa (Buni keyinroq app.js da ulaymiz)
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"Groq API xatoligi: {error_msg}")
        return {
            "overall_band": "XATO",
            "grammar_feedback": "AI xizmati bilan ulanishda xatolik yuz berdi.",
            "vocabulary_feedback": "Sabab:",
            "coherence_feedback": error_msg,
            "general_feedback": f"Groq xatosi: {error_msg}"
        }

@app.post("/api/speak")
async def check_speaking(audio: UploadFile = File(...), target_text: str = Form(...)):
    if not client:
        return {"error": "GROQ API kaliti ulanmagan!"}
        
    try:
        file_contents = await audio.read()
        
        # 1. Transcribe the audio using Groq's whisper model
        transcription = client.audio.transcriptions.create(
            file=("audio.webm", file_contents),
            model="whisper-large-v3",
            response_format="json",
        )
        
        transcript = transcription.text
        
        # 2. Score pronunciation by asking LLaMA
        prompt = f"""
        Siz Ingliz tili talaffuzini baholovchi mutaxassissiz.
        O'quvchi quyidagi gapni o'qishi kerak edi:
        "{target_text}"
        
        O'quvchi aytgan gap (AI eshitgan matn):
        "{transcript}"
        
        Iltimos, o'quvchining talaffuziga 0 dan 100% gacha baho bering va qisqacha izoh yozing.
        Agar gap umuman o'xshamasa, past foiz bering.
        Javob faqat ushbu JSON formatda bo'lsin:
        {{
            "score": "Masalan: 85%",
            "transcript": "{transcript}",
            "feedback": "Talaffuz bo'yicha maslahat yoki maqtov (O'zbek tilida)"
        }}
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        res_text = chat_completion.choices[0].message.content.strip()
        if res_text.startswith("```json"):
            res_text = res_text[7:-3].strip()
        elif res_text.startswith("```"):
            res_text = res_text[3:-3].strip()
            
        result = json.loads(res_text)
        return result
        
    except Exception as e:
        return {"error": f"Gapirishni tekshirishda xatolik: {str(e)}"}

@app.post("/api/evaluate_speaking")
async def evaluate_speaking(
    part: str = Form(...),
    topic: str = Form(...),
    questions: str = Form(...), # JSON list of questions
    audios: list[UploadFile] = File(...)
):
    if not client:
        return {
            "error": "GROQ API kaliti ulanmagan!",
            "overall_score": "N/A",
            "detailed_scores": {"fluency": "0%", "pronunciation": "0%", "vocabulary": "0%", "grammar": "0%"},
            "transcripts": ["API key missing"],
            "feedback": "DIQQAT: Backendda GROQ_API_KEY topilmadi! Ovoz tahlili imkonsiz."
        }
        
    try:
        # Parse questions from JSON string
        questions_list = json.loads(questions)
        
        # Concurrently transcribe all uploaded audios
        async def transcribe_one(audio_file: UploadFile, index: int):
            contents = await audio_file.read()
            filename = audio_file.filename if audio_file.filename else f"part_{part}_q_{index}.webm"
            # Groq's transcriptions endpoint
            transcription = client.audio.transcriptions.create(
                file=(filename, contents),
                model="whisper-large-v3",
                response_format="json",
            )
            return transcription.text
        
        import asyncio
        tasks = [transcribe_one(audio, idx) for idx, audio in enumerate(audios)]
        transcripts = await asyncio.gather(*tasks)
        
        # Formulate pairs for the prompt
        q_a_pairs_str = ""
        for idx, (q, t) in enumerate(zip(questions_list, transcripts)):
            q_a_pairs_str += f"\nSavol {idx+1}: {q}\nTalaba javobi: \"{t}\"\n"
            
        prompt = f"""
        Siz CEFR (DTM Multi-level) va IELTS standardlari bo'yicha professional Ingliz tili imtihon oluvchi (examiner) va malakali o'qituvchisiz.
        Talaba quyidagi gapirish imtihoni topshirig'ini bajardi:
        
        Imtihon qismi (Part): {part}
        Mavzu (Topic): {topic}
        
        Savollar va talabaning ovozli javoblaridan olingan matnlar (transcripts):
        {q_a_pairs_str}
        
        Quyidagi mezonlar asosida talabaning nutqini tahlil qiling:
        1. **Fluency & Coherence** (Ravonlik va izchillik): Nutqning ravonligi, to'xtalishlar, takrorlashlar, gaplar o'rtasidagi mantiqiy bog'liqlik.
        2. **Pronunciation** (Talaffuz): So'zlarning to'g'ri talaffuz qilinishi va intonatsiya.
        3. **Lexical Resource** (So'z boyligi): Mavzuga oid so'zlar va iboralar qo'llanishi, so'z takrorlaridan qochish.
        4. **Grammatical Range & Accuracy** (Grammatik boylik va aniqlik): Grammatik xatolar, gaplar tuzilishi (sodda va murakkab gaplar).
        
        Iltimos, har bir mezon uchun 0 dan 100% gacha bo'lgan foiz ko'rsatkichida baho bering va umumiy natijaviy darajani (masalan, B1, B2, A2, C1) belgilang.
        
        Barcha tavsiyalaringiz va izohlaringizni **O'zbek tilida** yozing. Izohda talabaning asosiy xatolarini (grammatika, talaffuz) ko'rsating va ularni tuzatish bo'yicha aniq maslahat bering.
        
        Javobni faqat va faqat quyidagi JSON formatida qaytaring (hech qanday boshqa so'zlarsiz, markdown blocksiz):
        {{
            "overall_score": "Masalan: B1 yoki B2 (baho)",
            "detailed_scores": {{
                "fluency": "Masalan: 75%",
                "pronunciation": "Masalan: 80%",
                "vocabulary": "Masalan: 70%",
                "grammar": "Masalan: 65%"
            }},
            "transcripts": {json.dumps(transcripts)},
            "feedback": "Mavzu bo'yicha umumiy fikr, talabaning yutuq va kamchiliklari, grammatik va talaffuz xatolar tahlili hamda yaxshilash bo'yicha o'zbek tilidagi tavsiyalar."
        }}
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.15
        )
        
        res_text = chat_completion.choices[0].message.content.strip()
        if res_text.startswith("```json"):
            res_text = res_text[7:-3].strip()
        elif res_text.startswith("```"):
            res_text = res_text[3:-3].strip()
            
        result = json.loads(res_text)
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Gapirishni tahlil qilishda xatolik: {str(e)}"}
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.get("/admin")
async def read_admin():
    return FileResponse("admin.html")

app.mount("/", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

