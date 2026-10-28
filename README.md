<div align="center">
  <h1>📚 LingoReader AI & LingoTutor</h1>
  <p><strong>Google Gemini SSE Streaming, OpenAI Whisper ASR ve İnteraktif Okuma Destekli Yapay Zeka İngilizce Öğrenme Platformu</strong></p>
  
  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-SSE_Streaming_API-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![Whisper](https://img.shields.io/badge/OpenAI_Whisper-ASR_Transcription-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
  [![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
  [![JavaScript](https://img.shields.io/badge/Frontend-SPA_HTML5_%2F_JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)]()
</div>

<br>

## 📖 Proje Hakkında
**LingoReader AI (LingoProje)**, yabancı dil öğrenimini pasif ezberden çıkarıp etkileşimli bir deneyime dönüştüren uçtan uca bir yapay zeka dil platformudur. Uygulama; **PDF/Metin İnteraktif Okuyucu**, **OpenAI Whisper + yt-dlp tabanlı YouTube Müzik/Video Karaoke Senkronizasyonu** ve **Server-Sent Events (SSE)** üzerinden gerçek zamanlı akış (streaming) sağlayan **LingoTutor AI (Google Gemini)** modüllerini tek bir modern SPA arayüzünde birleştirir.

---

## ✨ Temel Özellikler & Teknik Mimari

### 1. 📖 İnteraktif Okuyucu, PDF Ayrıştırıcı & Akıllı Sözlük
- **PDF.js Entegrasyonu:** Kullanıcılar İngilizce hikaye/makale PDF'lerini yükleyebilir veya doğrudan metin yapıştırabilir.
- **Tıklanabilir Kelime Motoru:** Metindeki her kelime dinamik olarak tokenize edilir; tıklandığında anında Türkçe çevirisi görüntülenir ve kişisel kelime defterine (`localStorage`) kaydedilir.
- **Sesli Okuma (Web Speech TTS):** `0.5x` – `2.0x` arasında ayarlanabilir hız kontrolü ile metinleri doğal telaffuzla seslendirir.
- **Bağlamsal Özetleme & "Hocaya Sor":** Seçilen kelime veya paragraf, aktif ekran bağlamıyla birlikte tek tıkla LingoTutor AI'a gönderilerek cümle içi kullanım, eş/zıt anlam ve gramer analizi alınır.

### 2. 🎵 AI Müzik & Karaoke Senkronizasyonu (`OpenAI Whisper` + `yt-dlp`)
- **Otonom Ses Çıkarımı:** Girilen YouTube URL'sinden `yt-dlp` ve otomatik keşfedilen `FFmpeg` hattı ile ses akışı indirilir.
- **Zaman Damgalı ASR (Automatic Speech Recognition):** **OpenAI Whisper (`base`)** modeli CPU/GPU uyumlu (`fp16=False`) olarak çalıştırılarak milisaniye hassasiyetinde segment zaman damgaları (`start`, `end`, `text`) çıkarılır.
- **Canlı Karaoke Akışı:** YouTube IFrame API ile video oynatılırken ilgili satır gerçek zamanlı vurgulanır; herhangi bir satıra tıklandığında video doğrudan o saniyeye (`seekTo`) atlar.

### 3. 🤖 LingoTutor AI — Gerçek Zamanlı SSE Streaming Öğretmen (`/chat`)
- **Çok Turlu Hafıza & Ekran Bağlamı Enjeksiyonu:** Son 12 mesajlık konuşma geçmişini (`history`) ve kullanıcının o an ekranda okuduğu hikayeyi veya dinlediği şarkı sözlerini (`context`) sistem istemine enjekte eder.
- **Düşük Gecikmeli SSE Akışı (`text/event-stream`):** Flask `stream_with_context` ve Gemini `streamGenerateContent` uç noktası ile yanıtları kelime kelime gerçek zamanlı akıtır.
- **Çoklu Model Yedekliliği (Fallback):** `gemini-2.5-flash` ➔ `gemini-2.0-flash` ➔ `gemini-1.5-flash` otomatik hata toleransı ile kesintisiz hizmet verir.

---

## 🚀 Kurulum ve Çalıştırma

### 1. Repoyu Klonlayın
```bash
git clone https://github.com/talha4111/LingoProje.git
cd LingoProje
```

### 2. Bağımlılıkları Yükleyin ve Ortamı Doğrulayın
```bash
pip install -r requirements.txt
python duzelt.py
```

### 3. Ortam Değişkenlerini Yapılandırın (`.env`)
`.env.example` dosyasını `.env` olarak kopyalayın ve Gemini API anahtarınızı ekleyin (veya doğrudan uygulama arayüzündeki **API Anahtarı** penceresinden girin):
```bash
cp .env.example .env
```
```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=5001
```

### 4. Uygulamayı Başlatın
Windows üzerinde tek tıkla başlatmak için `baslat.bat` dosyasını çalıştırabilir veya terminalden başlatabilirsiniz:
```bash
python api.py
```
Tarayıcınızda `http://localhost:5001` adresine gidin.

---

## 📂 Proje Klasör Yapısı
```text
LingoProje/
├── api.py             # Flask backend: Whisper ASR (/analyze), Gemini SSE Streaming (/chat) ve FFmpeg yönetimi
├── index.html         # İnteraktif Okuyucu, PDF.js, YouTube Karaoke ve LingoTutor SPA arayüzü
├── duzelt.py          # Python paketleri, FFmpeg ve Whisper model bütünlüğü tanılama aracı
├── baslat.bat         # Tek tıkla sunucu ve tarayıcı başlatıcı (Windows)
├── .env.example       # Örnek ortam değişkenleri şablonu
└── requirements.txt   # Python bağımlılıkları
```

---

## 👨‍💻 Geliştirici
**Talha Gürler** — [GitHub (@talha4111)](https://github.com/talha4111)
