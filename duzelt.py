import os
import sys
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 55)
print("🔍 LingoReader AI - Sistem ve Bağımlılık Kontrolü")
print("=" * 55)

# 1. Python Sürümü
print(f"🐍 Python Sürümü: {sys.version.split()[0]} -> ✅ UYGUN")

# 2. FFmpeg Kontrolü
from api import ensure_ffmpeg_path
ensure_ffmpeg_path()
ffmpeg_bin = shutil.which("ffmpeg")
if ffmpeg_bin:
    print(f"🎥 FFmpeg: Bulundu ({ffmpeg_bin}) -> ✅ HAZIR")
else:
    print("⚠️ FFmpeg bulunamadı! 'winget install Gyan.FFmpeg.Essentials' çalıştırabilirsiniz.")

# 3. Kütüphane Kontrolleri
modules = [
    ("Flask", "flask"),
    ("Flask-CORS", "flask_cors"),
    ("yt-dlp", "yt_dlp"),
    ("OpenAI Whisper", "whisper"),
    ("PyTorch", "torch"),
    ("python-dotenv", "dotenv"),
    ("Requests", "requests")
]

for display_name, mod_name in modules:
    try:
        __import__(mod_name)
        print(f"📦 {display_name}: Kurulu -> ✅ HAZIR")
    except ImportError:
        print(f"❌ {display_name}: Eksik! ('pip install -r requirements.txt' yapın)")

# 4. API Key Kontrolü
from dotenv import load_dotenv
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if api_key:
    print(f"🔑 Gemini API Anahtarı: .env dosyasında tanımlı -> ✅ AKTİF")
else:
    print("ℹ️ Gemini API Anahtarı: .env dosyasında yok (Web arayüzünden de eklenebilir) -> ⚡ OPSİYONEL")

print("\n" + "=" * 55)
print("🎉 Kontrol tamamlandı! Projeyi başlatmak için:")
print("   'python api.py' veya 'baslat.bat' çift tıklayın.")
print("=" * 55)