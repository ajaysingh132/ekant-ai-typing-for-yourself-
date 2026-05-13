"""
╔══════════════════════════════════════════════════════════════╗
║        एकांत इंटरनेशनल AI टाइपिंग सिस्टम                   ║
║        EKAANT INTERNATIONAL AI TYPING SYSTEM                 ║
║        GBSB4U Publications — Bhopal                          ║
╚══════════════════════════════════════════════════════════════╝

Author  : Ajay Singh Chauhan
Version : 2.0.0
"""

import os
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# ─── App Configuration ────────────────────────────────────────
app = FastAPI(
    title="एकांत AI टाइपिंग सिस्टम",
    description="Voice Typing + Image-to-Text OCR | GBSB4U Publications",
    version="2.0.0",
)

# ─── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Config: Load API Key from Environment ────────────────────
OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")
OCR_API_URL = "https://api.ocr.space/parse/image"


# ─── Root Endpoint ────────────────────────────────────────────
@app.get("/", tags=["System"])
def home():
    """System health check."""
    return {
        "status": "✅ Running",
        "system": "एकांत AI टाइपिंग सिस्टम",
        "version": "2.0.0",
        "publisher": "GBSB4U Publications, Bhopal",
    }


# ─── OCR Endpoint ────────────────────────────────────────────
@app.post("/ocr", tags=["OCR"])
async def ocr_endpoint(file: UploadFile = File(...)):
    """
    Performs OCR on uploaded image.
    Supports Hindi (hin) and English (eng) text recognition.
    """
    if not OCR_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OCR API Key कॉन्फ़िगर नहीं है। Server admin से संपर्क करें।",
        )

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"फ़ाइल प्रकार '{file.content_type}' समर्थित नहीं है। JPG/PNG/GIF/BMP/TIFF उपयोग करें।",
        )

    contents = await file.read()

    # File size check (max 1 MB for free OCR tier)
    if len(contents) > 1_000_000:
        raise HTTPException(
            status_code=413,
            detail="फ़ाइल बहुत बड़ी है। 1 MB से कम की image upload करें।",
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OCR_API_URL,
                files={"file": (file.filename, contents, file.content_type)},
                data={
                    "apikey": OCR_API_KEY,
                    "language": "eng",        # eng works for both Hindi & English in OCR.space
                    "isOverlayRequired": "false",
                    "detectOrientation": "true",
                    "scale": "true",
                    "OCREngine": "2",          # Engine 2 = more accurate
                },
            )
            response.raise_for_status()

        result = response.json()

        # Check API-level errors
        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage", ["Unknown OCR error"])[0]
            raise HTTPException(
                status_code=422,
                detail=f"OCR प्रोसेसिंग विफल: {error_msg}",
            )

        # Extract text safely
        parsed = result.get("ParsedResults")
        if not parsed or not isinstance(parsed, list):
            raise HTTPException(
                status_code=422,
                detail="OCR से कोई परिणाम नहीं मिला। स्पष्ट image try करें।",
            )

        text = parsed[0].get("ParsedText", "").strip()
        if not text:
            raise HTTPException(
                status_code=422,
                detail="Image में कोई text नहीं मिला।",
            )

        return {
            "success": True,
            "text": text,
            "filename": file.filename,
            "characters": len(text),
            "words": len(text.split()),
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="OCR सर्वर ने समय पर जवाब नहीं दिया। पुनः प्रयास करें।",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"OCR सर्वर से कनेक्ट नहीं हो सका: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"अप्रत्याशित त्रुटि: {str(e)}",
        )


# ─── UI Endpoint ─────────────────────────────────────────────
@app.get("/ui", response_class=HTMLResponse, tags=["Interface"])
def ui():
    """Serves the full interactive HTML interface."""
    return HTML_UI


# ─── HTML UI ─────────────────────────────────────────────────
HTML_UI = """<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>एकांत AI टाइपिंग सिस्टम</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Tiro+Devanagari+Hindi:ital@0;1&family=Cinzel+Decorative:wght@700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet" />

  <style>
    /* ── Variables ── */
    :root {
      --bg:        #080c14;
      --surface:   #0d1424;
      --panel:     #111927;
      --border:    rgba(180, 140, 60, 0.25);
      --gold:      #c9a84c;
      --gold-light:#e8cb7a;
      --gold-dim:  rgba(201, 168, 76, 0.15);
      --teal:      #38bdf8;
      --teal-dim:  rgba(56, 189, 248, 0.12);
      --text:      #e8dfc8;
      --text-muted:#8a7d65;
      --success:   #4ade80;
      --danger:    #f87171;
      --font-head: 'Cinzel Decorative', serif;
      --font-body: 'Tiro Devanagari Hindi', serif;
      --font-mono: 'JetBrains Mono', monospace;
      --radius:    12px;
      --glow:      0 0 30px rgba(201,168,76,0.15);
    }

    /* ── Reset ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 3px; }

    /* ── Body ── */
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-body);
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* ── Animated Background ── */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background:
        radial-gradient(ellipse 60% 40% at 20% 10%, rgba(201,168,76,0.06) 0%, transparent 70%),
        radial-gradient(ellipse 40% 60% at 80% 90%, rgba(56,189,248,0.05) 0%, transparent 70%);
      pointer-events: none;
      z-index: 0;
    }

    /* ── Mandala Background Pattern ── */
    body::after {
      content: '';
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 800px;
      height: 800px;
      background-image:
        repeating-conic-gradient(
          from 0deg,
          rgba(201,168,76,0.025) 0deg 10deg,
          transparent 10deg 20deg
        );
      border-radius: 50%;
      pointer-events: none;
      z-index: 0;
      animation: rotateMandala 60s linear infinite;
    }

    @keyframes rotateMandala {
      to { transform: translate(-50%, -50%) rotate(360deg); }
    }

    /* ── Wrapper ── */
    .wrapper {
      position: relative;
      z-index: 1;
      max-width: 880px;
      margin: 0 auto;
      padding: 40px 20px 80px;
    }

    /* ── Header ── */
    .header {
      text-align: center;
      margin-bottom: 52px;
      animation: fadeDown 0.8s ease both;
    }

    .header-badge {
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 10px;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: var(--gold);
      border: 1px solid var(--border);
      padding: 5px 16px;
      border-radius: 20px;
      margin-bottom: 20px;
      background: var(--gold-dim);
    }

    .header h1 {
      font-family: var(--font-head);
      font-size: clamp(22px, 5vw, 38px);
      color: var(--gold-light);
      letter-spacing: 2px;
      text-shadow: 0 0 40px rgba(201,168,76,0.4);
      line-height: 1.2;
      margin-bottom: 8px;
    }

    .header-sub {
      font-family: var(--font-body);
      font-size: 16px;
      color: var(--text-muted);
      font-style: italic;
    }

    .header-line {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-top: 24px;
      justify-content: center;
    }

    .header-line::before,
    .header-line::after {
      content: '';
      flex: 1;
      max-width: 200px;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }

    .header-line span {
      color: var(--gold);
      font-size: 20px;
    }

    /* ── Stat Bar ── */
    .stat-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 32px;
      animation: fadeUp 0.8s 0.1s ease both;
    }

    .stat-chip {
      flex: 1;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 14px 16px;
      text-align: center;
    }

    .stat-chip .val {
      display: block;
      font-family: var(--font-mono);
      font-size: 22px;
      font-weight: 700;
      color: var(--gold-light);
      transition: all 0.3s;
    }

    .stat-chip .lbl {
      font-size: 11px;
      color: var(--text-muted);
      letter-spacing: 1px;
      text-transform: uppercase;
    }

    /* ── Tabs ── */
    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 28px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 6px;
      animation: fadeUp 0.8s 0.15s ease both;
    }

    .tab-btn {
      flex: 1;
      background: transparent;
      border: none;
      padding: 12px 16px;
      color: var(--text-muted);
      font-family: var(--font-body);
      font-size: 14px;
      cursor: pointer;
      border-radius: 8px;
      transition: all 0.25s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .tab-btn:hover { color: var(--gold); background: var(--gold-dim); }

    .tab-btn.active {
      background: linear-gradient(135deg, rgba(201,168,76,0.25), rgba(201,168,76,0.1));
      color: var(--gold-light);
      border: 1px solid var(--border);
      box-shadow: var(--glow);
    }

    .tab-icon { font-size: 18px; }

    /* ── Panel ── */
    .tab-panel { display: none; animation: fadeUp 0.4s ease both; }
    .tab-panel.active { display: block; }

    /* ── Card ── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 28px;
      margin-bottom: 20px;
      position: relative;
      overflow: hidden;
    }

    .card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }

    .card-title {
      font-family: var(--font-mono);
      font-size: 11px;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: var(--gold);
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* ── Textarea ── */
    .output-area {
      width: 100%;
      min-height: 160px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      color: var(--text);
      font-family: var(--font-body);
      font-size: 16px;
      line-height: 1.8;
      resize: vertical;
      transition: border-color 0.2s, box-shadow 0.2s;
      outline: none;
    }

    .output-area:focus {
      border-color: var(--gold);
      box-shadow: 0 0 0 3px rgba(201,168,76,0.1);
    }

    .output-area::placeholder { color: var(--text-muted); font-style: italic; }

    /* ── Voice Section ── */
    .voice-center { text-align: center; padding: 10px 0 24px; }

    .mic-ring {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 96px;
      height: 96px;
      border-radius: 50%;
      background: var(--gold-dim);
      border: 2px solid var(--border);
      cursor: pointer;
      transition: all 0.3s;
      position: relative;
      margin-bottom: 16px;
    }

    .mic-ring:hover {
      background: rgba(201,168,76,0.25);
      border-color: var(--gold);
      transform: scale(1.05);
      box-shadow: 0 0 30px rgba(201,168,76,0.3);
    }

    .mic-ring.listening {
      background: rgba(248,113,113,0.15);
      border-color: var(--danger);
      animation: micPulse 1.2s ease infinite;
    }

    .mic-ring.listening::before {
      content: '';
      position: absolute;
      inset: -8px;
      border-radius: 50%;
      border: 2px solid rgba(248,113,113,0.4);
      animation: micRipple 1.2s ease infinite;
    }

    @keyframes micPulse {
      0%, 100% { box-shadow: 0 0 20px rgba(248,113,113,0.3); }
      50%       { box-shadow: 0 0 40px rgba(248,113,113,0.6); }
    }

    @keyframes micRipple {
      0%   { transform: scale(1); opacity: 1; }
      100% { transform: scale(1.4); opacity: 0; }
    }

    .mic-icon { font-size: 36px; }

    .mic-status {
      font-family: var(--font-mono);
      font-size: 12px;
      letter-spacing: 1px;
      color: var(--text-muted);
      margin-bottom: 20px;
    }

    .mic-status.active { color: var(--danger); }

    /* ── Language Toggle ── */
    .lang-toggle {
      display: inline-flex;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 20px;
    }

    .lang-btn {
      padding: 8px 20px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .lang-btn.active {
      background: var(--gold-dim);
      color: var(--gold-light);
    }

    /* ── OCR Drop Zone ── */
    .drop-zone {
      border: 2px dashed var(--border);
      border-radius: var(--radius);
      padding: 40px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.25s;
      position: relative;
      margin-bottom: 20px;
    }

    .drop-zone:hover,
    .drop-zone.drag-over {
      border-color: var(--gold);
      background: var(--gold-dim);
    }

    .drop-zone input[type=file] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
    }

    .drop-icon { font-size: 48px; margin-bottom: 12px; }

    .drop-text {
      color: var(--text-muted);
      font-size: 14px;
      line-height: 1.6;
    }

    .drop-text strong { color: var(--gold); }

    /* ── Image Preview ── */
    .img-preview {
      display: none;
      width: 100%;
      max-height: 220px;
      object-fit: contain;
      border-radius: 8px;
      border: 1px solid var(--border);
      margin-bottom: 16px;
    }

    .img-preview.show { display: block; }

    /* ── Buttons ── */
    .btn-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 11px 22px;
      border: none;
      border-radius: 8px;
      font-family: var(--font-body);
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
      font-weight: 600;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--gold), #a07828);
      color: #0d0a04;
    }

    .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(201,168,76,0.4); }

    .btn-ghost {
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-muted);
    }

    .btn-ghost:hover { border-color: var(--gold); color: var(--gold); }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none !important;
    }

    /* ── Progress Bar ── */
    .progress-bar {
      height: 3px;
      background: var(--border);
      border-radius: 2px;
      margin: 12px 0;
      overflow: hidden;
      display: none;
    }

    .progress-bar.show { display: block; }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--gold), var(--teal));
      border-radius: 2px;
      width: 0%;
      transition: width 0.3s;
      animation: progressAnim 1.5s ease infinite;
    }

    @keyframes progressAnim {
      0%   { background-position: 0% 50%; }
      100% { background-position: 100% 50%; }
    }

    /* ── Toast ── */
    .toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .toast {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 18px;
      font-size: 13px;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 10px;
      animation: toastIn 0.3s ease;
      min-width: 260px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }

    .toast.success { border-left: 3px solid var(--success); }
    .toast.error   { border-left: 3px solid var(--danger); }
    .toast.info    { border-left: 3px solid var(--gold); }

    @keyframes toastIn {
      from { transform: translateX(40px); opacity: 0; }
      to   { transform: translateX(0); opacity: 1; }
    }

    /* ── Footer ── */
    .footer {
      text-align: center;
      margin-top: 60px;
      color: var(--text-muted);
      font-size: 12px;
      font-family: var(--font-mono);
      letter-spacing: 1px;
    }

    .footer a { color: var(--gold); text-decoration: none; }

    /* ── History ── */
    .history-list { display: flex; flex-direction: column; gap: 10px; }

    .history-item {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 16px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      animation: fadeUp 0.3s ease;
    }

    .history-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }

    .history-text {
      flex: 1;
      font-size: 14px;
      line-height: 1.6;
      color: var(--text);
      white-space: pre-wrap;
      word-break: break-word;
    }

    .history-meta {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--text-muted);
      margin-top: 4px;
    }

    .history-copy {
      background: transparent;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 4px 10px;
      color: var(--text-muted);
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
      flex-shrink: 0;
    }

    .history-copy:hover { border-color: var(--gold); color: var(--gold); }

    /* ── Empty state ── */
    .empty {
      text-align: center;
      padding: 40px 20px;
      color: var(--text-muted);
      font-size: 14px;
    }

    /* ── Keyframes ── */
    @keyframes fadeDown {
      from { opacity: 0; transform: translateY(-20px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(20px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Mobile ── */
    @media (max-width: 600px) {
      .stat-bar { flex-wrap: wrap; }
      .stat-chip { flex: 1 1 calc(50% - 6px); }
      .btn-row { flex-direction: column; }
      .tab-btn { font-size: 12px; padding: 10px 8px; }
    }
  </style>
</head>
<body>

<!-- Toast Container -->
<div class="toast-container" id="toastContainer"></div>

<div class="wrapper">

  <!-- ── Header ── -->
  <div class="header">
    <div class="header-badge">GBSB4U Publications · Bhopal · v2.0</div>
    <h1>एकांत AI टाइपिंग सिस्टम</h1>
    <div class="header-sub">Ekaant International AI Typing System</div>
    <div class="header-line"><span>✦</span></div>
  </div>

  <!-- ── Stats ── -->
  <div class="stat-bar">
    <div class="stat-chip">
      <span class="val" id="statWords">0</span>
      <span class="lbl">शब्द</span>
    </div>
    <div class="stat-chip">
      <span class="val" id="statChars">0</span>
      <span class="lbl">अक्षर</span>
    </div>
    <div class="stat-chip">
      <span class="val" id="statOCR">0</span>
      <span class="lbl">OCR स्कैन</span>
    </div>
    <div class="stat-chip">
      <span class="val" id="statVoice">0</span>
      <span class="lbl">वॉइस सेशन</span>
    </div>
  </div>

  <!-- ── Tabs ── -->
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('voice', this)">
      <span class="tab-icon">🎤</span> वॉइस टाइपिंग
    </button>
    <button class="tab-btn" onclick="switchTab('ocr', this)">
      <span class="tab-icon">📷</span> Image to Text
    </button>
    <button class="tab-btn" onclick="switchTab('history', this)">
      <span class="tab-icon">📋</span> इतिहास
    </button>
  </div>

  <!-- ══ VOICE TAB ══ -->
  <div class="tab-panel active" id="tab-voice">
    <div class="card">
      <div class="card-title">🎤 वॉइस टाइपिंग</div>

      <!-- Language Toggle -->
      <div style="text-align:center">
        <div class="lang-toggle">
          <button class="lang-btn active" id="langHi" onclick="setLang('hi-IN', this)">हिंदी</button>
          <button class="lang-btn" id="langEn" onclick="setLang('en-US', this)">English</button>
          <button class="lang-btn" id="langMr" onclick="setLang('mr-IN', this)">मराठी</button>
        </div>
      </div>

      <!-- Mic Button -->
      <div class="voice-center">
        <div class="mic-ring" id="micRing" onclick="toggleVoice()">
          <span class="mic-icon" id="micIcon">🎤</span>
        </div>
        <div class="mic-status" id="micStatus">बोलना शुरू करने के लिए माइक दबाएं</div>
      </div>

      <!-- Output -->
      <div class="card-title">📝 टाइप किया गया टेक्स्ट</div>
      <textarea class="output-area" id="voiceOutput"
        placeholder="यहाँ आपकी आवाज़ टेक्स्ट में आएगी..."
        oninput="updateStats('voice')"></textarea>

      <div class="btn-row">
        <button class="btn btn-primary" onclick="copyText('voiceOutput')">📋 Copy करें</button>
        <button class="btn btn-ghost" onclick="clearText('voiceOutput')">🗑 Clear</button>
        <button class="btn btn-ghost" onclick="saveToHistory('voice')">💾 सहेजें</button>
      </div>
    </div>
  </div>

  <!-- ══ OCR TAB ══ -->
  <div class="tab-panel" id="tab-ocr">
    <div class="card">
      <div class="card-title">📷 Image to Text (OCR)</div>

      <!-- Drop Zone -->
      <div class="drop-zone" id="dropZone"
           ondragover="handleDrag(event, true)"
           ondragleave="handleDrag(event, false)"
           ondrop="handleDrop(event)">
        <input type="file" id="fileInput" accept="image/*" onchange="previewFile(event)" />
        <div class="drop-icon">🖼️</div>
        <div class="drop-text">
          <strong>Click करें या Image खींचें</strong><br />
          JPG · PNG · GIF · BMP · TIFF<br />
          <small>अधिकतम 1 MB</small>
        </div>
      </div>

      <img class="img-preview" id="imgPreview" alt="Preview" />

      <div class="progress-bar" id="ocrProgress">
        <div class="progress-fill"></div>
      </div>

      <div class="btn-row">
        <button class="btn btn-primary" id="ocrBtn" onclick="runOCR()">🔍 OCR चलाएं</button>
        <button class="btn btn-ghost" onclick="clearOCR()">🗑 Clear</button>
      </div>
    </div>

    <div class="card" id="ocrResultCard" style="display:none">
      <div class="card-title">📄 OCR परिणाम</div>
      <textarea class="output-area" id="ocrOutput"
        placeholder="OCR परिणाम यहाँ आएगा..."
        oninput="updateStats('ocr')"></textarea>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="copyText('ocrOutput')">📋 Copy करें</button>
        <button class="btn btn-ghost" onclick="saveToHistory('ocr')">💾 सहेजें</button>
      </div>
    </div>
  </div>

  <!-- ══ HISTORY TAB ══ -->
  <div class="tab-panel" id="tab-history">
    <div class="card">
      <div class="card-title" style="justify-content:space-between">
        <span>📋 सहेजा गया इतिहास</span>
        <button class="btn btn-ghost" style="padding:4px 12px;font-size:12px" onclick="clearHistory()">सब हटाएं</button>
      </div>
      <div class="history-list" id="historyList">
        <div class="empty">अभी कोई आइटम नहीं। वॉइस या OCR टेक्स्ट सहेजें।</div>
      </div>
    </div>
  </div>

  <!-- ── Footer ── -->
  <div class="footer">
    <p>एकांत इंटरनेशनल AI टाइपिंग सिस्टम · GBSB4U Publications · Bhopal</p>
    <p style="margin-top:6px">राज मिले या नाराज़गी — हम केवल सत्य के पक्ष में रहेंगे ✦</p>
  </div>
</div>

<script>
// ══════════════════════════════════════════
//  STATE
// ══════════════════════════════════════════
let currentLang = 'hi-IN';
let recognition  = null;
let isListening  = false;
let history      = JSON.parse(localStorage.getItem('ekaantHistory') || '[]');
let stats        = JSON.parse(localStorage.getItem('ekaantStats') || '{"ocr":0,"voice":0}');

// ══════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  renderHistory();
  document.getElementById('statOCR').textContent   = stats.ocr;
  document.getElementById('statVoice').textContent = stats.voice;
});

// ══════════════════════════════════════════
//  TABS
// ══════════════════════════════════════════
function switchTab(name, btn) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}

// ══════════════════════════════════════════
//  VOICE TYPING
// ══════════════════════════════════════════
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function setLang(lang, btn) {
  currentLang = lang;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (isListening) { stopVoice(); startVoice(); }
}

function toggleVoice() {
  if (!SpeechRecognition) {
    toast('आपका ब्राउज़र Speech Recognition को सपोर्ट नहीं करता।', 'error');
    return;
  }
  isListening ? stopVoice() : startVoice();
}

function startVoice() {
  recognition = new SpeechRecognition();
  recognition.lang       = currentLang;
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onstart = () => {
    isListening = true;
    document.getElementById('micRing').classList.add('listening');
    document.getElementById('micIcon').textContent    = '⏹';
    document.getElementById('micStatus').textContent  = '● सुन रहा है...';
    document.getElementById('micStatus').className    = 'mic-status active';
  };

  let finalText = document.getElementById('voiceOutput').value;

  recognition.onresult = (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        finalText += e.results[i][0].transcript + ' ';
      } else {
        interim = e.results[i][0].transcript;
      }
    }
    document.getElementById('voiceOutput').value = finalText + interim;
    updateStats('voice');
  };

  recognition.onerror = (e) => {
    toast('माइक त्रुटि: ' + e.error, 'error');
    stopVoice();
  };

  recognition.onend = () => {
    if (isListening) recognition.start(); // auto-restart
  };

  recognition.start();
  stats.voice++;
  localStorage.setItem('ekaantStats', JSON.stringify(stats));
  document.getElementById('statVoice').textContent = stats.voice;
}

function stopVoice() {
  isListening = false;
  if (recognition) recognition.stop();
  document.getElementById('micRing').classList.remove('listening');
  document.getElementById('micIcon').textContent    = '🎤';
  document.getElementById('micStatus').textContent  = 'बोलना शुरू करने के लिए माइक दबाएं';
  document.getElementById('micStatus').className    = 'mic-status';
}

// ══════════════════════════════════════════
//  OCR
// ══════════════════════════════════════════
function previewFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    const img = document.getElementById('imgPreview');
    img.src = ev.target.result;
    img.classList.add('show');
  };
  reader.readAsDataURL(file);
  document.querySelector('.drop-text').innerHTML =
    '<strong>' + file.name + '</strong><br><small>' +
    (file.size / 1024).toFixed(1) + ' KB</small>';
}

function handleDrag(e, over) {
  e.preventDefault();
  document.getElementById('dropZone').classList.toggle('drag-over', over);
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropZone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    document.getElementById('fileInput').files = dt.files;
    previewFile({ target: { files: dt.files } });
  }
}

async function runOCR() {
  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files[0]) {
    toast('पहले कोई image चुनें।', 'error'); return;
  }

  const btn      = document.getElementById('ocrBtn');
  const progress = document.getElementById('ocrProgress');
  btn.disabled   = true;
  btn.textContent = '⏳ प्रोसेस हो रहा है...';
  progress.classList.add('show');

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  try {
    const res  = await fetch('/ocr', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      toast(data.detail || 'OCR विफल रहा।', 'error');
    } else {
      document.getElementById('ocrOutput').value = data.text;
      document.getElementById('ocrResultCard').style.display = 'block';
      updateStats('ocr');
      stats.ocr++;
      localStorage.setItem('ekaantStats', JSON.stringify(stats));
      document.getElementById('statOCR').textContent = stats.ocr;
      toast('✅ OCR सफल! ' + data.words + ' शब्द मिले।', 'success');
    }
  } catch (err) {
    toast('नेटवर्क त्रुटि: ' + err.message, 'error');
  } finally {
    btn.disabled    = false;
    btn.textContent = '🔍 OCR चलाएं';
    progress.classList.remove('show');
  }
}

function clearOCR() {
  document.getElementById('fileInput').value = '';
  document.getElementById('imgPreview').classList.remove('show');
  document.getElementById('ocrOutput').value = '';
  document.getElementById('ocrResultCard').style.display = 'none';
  document.querySelector('.drop-text').innerHTML =
    '<strong>Click करें या Image खींचें</strong><br/>JPG · PNG · GIF · BMP · TIFF<br/><small>अधिकतम 1 MB</small>';
  updateStats('ocr');
}

// ══════════════════════════════════════════
//  STATS
// ══════════════════════════════════════════
function updateStats(type) {
  const id   = type === 'voice' ? 'voiceOutput' : 'ocrOutput';
  const text = document.getElementById(id).value.trim();
  const words = text ? text.split(/\s+/).length : 0;
  document.getElementById('statWords').textContent = words;
  document.getElementById('statChars').textContent = text.length;
}

// ══════════════════════════════════════════
//  HISTORY
// ══════════════════════════════════════════
function saveToHistory(type) {
  const id   = type === 'voice' ? 'voiceOutput' : 'ocrOutput';
  const text = document.getElementById(id).value.trim();
  if (!text) { toast('कोई टेक्स्ट नहीं है सहेजने के लिए।', 'error'); return; }
  history.unshift({ type, text, time: new Date().toLocaleString('hi-IN') });
  if (history.length > 50) history.pop();
  localStorage.setItem('ekaantHistory', JSON.stringify(history));
  renderHistory();
  toast('✅ इतिहास में सहेजा गया।', 'success');
}

function renderHistory() {
  const list = document.getElementById('historyList');
  if (!history.length) {
    list.innerHTML = '<div class="empty">अभी कोई आइटम नहीं। वॉइस या OCR टेक्स्ट सहेजें।</div>';
    return;
  }
  list.innerHTML = history.map((item, i) => `
    <div class="history-item">
      <span class="history-icon">${item.type === 'voice' ? '🎤' : '📷'}</span>
      <div style="flex:1">
        <div class="history-text">${item.text.substring(0, 200)}${item.text.length > 200 ? '...' : ''}</div>
        <div class="history-meta">${item.time} · ${item.text.split(/\s+/).length} शब्द</div>
      </div>
      <button class="history-copy" onclick="copyDirect(${i})">Copy</button>
    </div>
  `).join('');
}

function copyDirect(i) {
  navigator.clipboard.writeText(history[i].text)
    .then(() => toast('📋 Copy हो गया!', 'success'))
    .catch(() => toast('Copy विफल।', 'error'));
}

function clearHistory() {
  if (!confirm('सारा इतिहास हटाएं?')) return;
  history = [];
  localStorage.setItem('ekaantHistory', JSON.stringify(history));
  renderHistory();
  toast('इतिहास साफ हो गया।', 'info');
}

// ══════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════
function copyText(id) {
  const text = document.getElementById(id).value;
  if (!text) { toast('कॉपी करने के लिए कोई टेक्स्ट नहीं है।', 'error'); return; }
  navigator.clipboard.writeText(text)
    .then(() => toast('📋 Copy हो गया!', 'success'))
    .catch(() => toast('Copy विफल।', 'error'));
}

function clearText(id) {
  document.getElementById(id).value = '';
  updateStats(id === 'voiceOutput' ? 'voice' : 'ocr');
}

function toast(msg, type = 'info') {
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.innerHTML = (type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️') + ' ' + msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}
</script>
</body>
</html>
"""


# ─── Run Instructions ─────────────────────────────────────────
"""
📦 Installation:
    pip install fastapi uvicorn httpx python-multipart

🔑 Set API Key (optional):
    Linux/Mac : export OCR_API_KEY=your_key_here
    Windows   : set OCR_API_KEY=your_key_here

🚀 Run Server:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

🌐 Access:
    UI  → http://127.0.0.1:8000/ui
    API → http://127.0.0.1:8000/ocr  (POST)
    Docs→ http://127.0.0.1:8000/docs
"""
