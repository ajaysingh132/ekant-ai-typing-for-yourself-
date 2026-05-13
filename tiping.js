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
