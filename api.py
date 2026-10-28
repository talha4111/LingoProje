import os
import sys
import re
import json
import shutil
import requests

# Windows konsolunda UTF-8 karakter desteği sağla
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

# FFmpeg yolunu kontrol et ve gerekiyorsa PATH'e ekle
def ensure_ffmpeg_path():
    if shutil.which("ffmpeg"):
        return
    # WinGet Gyan FFmpeg varsayılan konumu kontrolü
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    possible_paths = [
        os.path.join(local_app_data, "Microsoft", "WinGet", "Packages"),
        "C:\\Program Files\\ffmpeg\\bin",
        "C:\\ffmpeg\\bin"
    ]
    for base in possible_paths:
        if os.path.exists(base):
            for root, _, files in os.walk(base):
                if "ffmpeg.exe" in files:
                    os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")
                    print(f"✅ FFmpeg bulundu ve PATH'e eklendi: {root}")
                    return

ensure_ffmpeg_path()

# Global Whisper Modeli (Lazy Loading)
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        import whisper
        print("⏳ Whisper modeli (base) yükleniyor...")
        whisper_model = whisper.load_model("base")
        print("✅ Whisper modeli hazır!")
    return whisper_model

# --- SİSTEM PROMPTU (LINGOTUTOR AI) ---
LINGO_SYSTEM_PROMPT = """Sen 'LingoTutor' adında yardımsever, sevecen, teşvik edici ve uzman bir İngilizce öğretmenisin.
Kullanıcının İngilizceyi en keyifli, akıcı ve kalıcı şekilde öğrenmesine yardım ediyorsun.

ÖNEMLİ KURALLAR VE DAVRANIŞLARIN:
1. HAFIZA VE SOHBET SÜREKLİLİĞİ:
   - Önceki mesajları, kullanıcının az önce sorduğu soruları, yaptığı hataları ve öğrendiği kelimeleri mutlaka hatırla.
   - Kullanıcı "az önce sorduğum...", "bunun yerine...", "peki bu?" gibi devam soruları sorduğunda konuşmanın bağlamını koru ve önceki konudan kopma.

2. EKRANDAKİ İÇERİK & BAĞLAM FARKINDALIĞI:
   - Kullanıcı sayfada bir hikaye okuyorsa veya bir YouTube şarkısı dinliyorsa, ekrandaki içerik sana iletilecektir.
   - Sorulan soruları o içerikteki anlama ve bağlama göre açıkla.

3. KELİME / KALIP / DEYİM SORULARI:
   - Kelimenin/deyimin Türkçe anlamını net ve dolaysız ver.
   - Günlük hayattan 2-3 adet doğal İngilizce örnek cümle ve Türkçe çevirisini sun.
   - Varsa yaygın eş anlamlılarını (synonyms) veya zıt anlamlılarını (antonyms) belirt.

4. CÜMLE DÜZELTME & GERİ BİLDİRİM:
   - Kullanıcı İngilizce yazdığında gramer, yazım veya edat hatalarını nazikçe göster.
   - Cümlenin çok daha doğal / yerli (native) kullanımını paylaş.
   - Neden öyle olması gerektiğini kısa ve anlaşılır bir Türkçe ile açıkla.

5. PRATİK & SOHBET:
   - Kullanıcı İngilizce sohbet ediyorsa, konuşmayı samimi ve akıcı bir İngilizceyle sürdür.
   - Kullanıcının konuşmaya devam edebilmesi için mesajının sonuna merak uyandıran bir soru ekle.
   - Hataları varsa sohbetin akışını bozmadan cevabının en sonuna '💡 Küçük İpucu: ...' şeklinde ekle.

BİÇİMLENDİRME:
- Cevaplarını okunması çok kolay, estetik Markdown formatında hazırla (başlıklar, kalın yazılar, emojiler, madde işaretleri kullan).
- Gereksiz uzun ansiklopedi metinleri yazma; samimi bir özel ders hocası gibi net, canlı ve motive edici ol.
"""

# --- 1. SİTEYİ SUNMA ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# --- 2. SİSTEM DURUMU ---
@app.route('/status', methods=['GET'])
def system_status():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    return jsonify({
        "status": "online",
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "has_env_api_key": bool(api_key),
        "whisper_ready": whisper_model is not None
    })

# --- 3. AKILLI & HAFIZALI LINGOTUTOR CHAT API (STREAMING DESTEKLİ) ---
@app.route('/chat', methods=['POST'])
def chat_with_ai():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    client_api_key = data.get('apiKey', '').strip()
    history = data.get('history', [])  # [{"role": "user"|"model", "text": "..."}]
    context = data.get('context', '').strip()
    want_stream = data.get('stream', True)
    
    if not user_message:
        return jsonify({"reply": "Lütfen bir mesaj veya soru yazın."})
    
    # API Anahtarı kontrolü
    api_key = client_api_key or os.environ.get("GEMINI_API_KEY", "").strip()
    
    if not api_key:
        return jsonify({
            "reply": (
                "👋 **Merhaba! Ben LingoTutor.**\n\n"
                "Seninle akıcı İngilizce pratik yapabilmem, sorularını yanıtlamam ve konuşmalarımızı hatırlayabilmem için bir **Google Gemini API Anahtarı** gerekiyor.\n\n"
                "🔑 **1 dakikada ücretsiz almak için:**\n"
                "1. [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) adresine gidin.\n"
                "2. Google hesabınızla giriş yapıp **'Create API key'** butonuna tıklayın.\n"
                "3. Üst kısımdaki **⚙️ API Ayarı** butonuna tıklayıp anahtarınızı yapıştırın.\n\n"
                "✨ Anahtarınızı girdiğinizde sınırsız ve kesintisiz çalışacağım!"
            ),
            "need_api_key": True
        })

    # Gemini için çok turlu (multi-turn) geçmişi yapılandır
    contents = []
    
    # Son 12 mesaja kadar geçmişi al (Hafıza)
    for msg in history[-12:]:
        if isinstance(msg, dict):
            r = "user" if msg.get("role") == "user" else "model"
            t = msg.get("text", "").strip()
            if t:
                contents.append({
                    "role": r,
                    "parts": [{"text": t}]
                })

    # Güncel mesaj (Varsa ekrandaki bağlam ile zenginleştir)
    current_text = user_message
    if context and len(context) > 10:
        current_text = f"[Ekrandaki İçerik Bağlamı]:\n\"\"\"{context[:1500]}\"\"\"\n\n[Kullanıcı Sorusu / Mesajı]:\n{user_message}"

    contents.append({
        "role": "user",
        "parts": [{"text": current_text}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": LINGO_SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    # Sırayla en hızlı ve güncel modelleri dene
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]

    if want_stream:
        def stream_generator():
            success = False
            for model_name in models_to_try:
                stream_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={api_key}"
                try:
                    with requests.post(stream_url, json=payload, headers={"Content-Type": "application/json"}, stream=True, timeout=25) as r:
                        if r.status_code == 200:
                            success = True
                            for line in r.iter_lines(decode_unicode=True):
                                if line and line.startswith("data: "):
                                    raw = line[6:].strip()
                                    if raw:
                                        try:
                                            chunk = json.loads(raw)
                                            t = chunk["candidates"][0]["content"]["parts"][0]["text"]
                                            yield f"data: {json.dumps({'text': t})}\n\n"
                                        except Exception:
                                            pass
                            yield "data: [DONE]\n\n"
                            break
                except Exception:
                    continue

            if not success:
                yield f"data: {json.dumps({'error': '⚠️ Yapay zekaya ulaşılamadı. Lütfen API anahtarınızı veya internet bağlantınızı kontrol edin.'})}\n\n"
                yield "data: [DONE]\n\n"

        return Response(stream_with_context(stream_generator()), mimetype='text/event-stream')

    else:
        # Non-streaming yedek
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            try:
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
                if res.status_code == 200:
                    t = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return jsonify({"reply": t})
            except Exception:
                continue
        return jsonify({"reply": "⚠️ Yapay zekaya ulaşılamadı. Lütfen API anahtarınızı kontrol edin."}), 500

# --- 4. YOUTUBE ANALİZ & KARAOKE TRANSKRİPT API ---
@app.route('/analyze', methods=['POST'])
def analyze():
    import yt_dlp
    import uuid
    
    data = request.json or {}
    raw_url = data.get('url', '').strip()
    if not raw_url:
        return jsonify({"error": "Lütfen geçerli bir YouTube linki girin."}), 400

    ensure_ffmpeg_path()
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return jsonify({"error": "Sistemde FFmpeg bulunamadı. Lütfen sunucuyu yeniden başlatın."}), 500
    
    ffmpeg_dir = os.path.dirname(ffmpeg_bin)

    # Video ID'yi regex ile güvenle çıkar
    vid_match = re.search(r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', raw_url)
    if vid_match:
        video_id = vid_match.group(1)
        url = f"https://www.youtube.com/watch?v={video_id}"
    else:
        url = raw_url

    file_id = uuid.uuid4().hex[:8]
    out_tmpl = f"audio_{file_id}.%(ext)s"
    audio_file = f"audio_{file_id}.mp3"
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_tmpl,
            'ffmpeg_location': ffmpeg_dir,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }
        
        print(f"📥 YouTube sesi indiriliyor: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if not os.path.exists(audio_file):
            return jsonify({"error": "YouTube ses dosyası indirilemedi veya dönüştürülemedi."}), 500

        print("🎙️ Whisper ile transkript çıkarılıyor...")
        model = get_whisper_model()
        # CPU'da sorunsuz çalışması için fp16=False
        result = model.transcribe(audio_file, fp16=False)

        segments_data = []
        for s in result.get("segments", []):
            segments_data.append({
                "start": round(s.get("start", 0), 2),
                "end": round(s.get("end", 0), 2),
                "text": s.get("text", "").strip()
            })

        print("✅ Transkript başarıyla oluşturuldu!")
        return jsonify({
            "videoId": video_id if vid_match else None,
            "text": result.get("text", ""),
            "segments": segments_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ YouTube analiz hatası: {e}", flush=True)
        return jsonify({"error": f"Analiz başarısız oldu: {str(e)}"}), 500
    finally:
        # Geçici dosyaları temizle
        for f in os.listdir("."):
            if f.startswith(f"audio_{file_id}"):
                try: os.remove(f)
                except: pass

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    print("=" * 50)
    print(f"🚀 LingoProje (LingoTutor AI) Başlatıldı!")
    print(f"🌐 Tarayıcınızda açın: http://localhost:{port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)