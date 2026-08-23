# Runova Print

Automated document-to-print pipeline for photocopy/printing shops.

> Customer uploads document photo → system auto-processes → shopkeeper confirms → print-ready PDF.

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
cp .env.example .env

# Initialize database
python ../scripts/setup_db.py

# Create a test shop
python ../scripts/seed_shop.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Customer Upload Page

Open in browser:

```
http://localhost:8000/frontend/index.html?shop_id=<SHOP_ID>
```

Or serve the frontend separately:

```bash
cd frontend
python -m http.server 3000
# Then open: http://localhost:3000/?shop_id=<SHOP_ID>
```

### Desktop Agent (Windows)

```bash
cd agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python runova_agent.py --server http://localhost:8000
```

## Architecture

```
Customer (Mobile)        FastAPI Server         Desktop Agent (Windows)
     │                        │                        │
     │  POST /upload          │                        │
     │───────────────────►    │                        │
     │                        │  Process Image         │
     │                        │  (OpenCV + OCR)        │
     │                        │                        │
     │                        │  WebSocket notify      │
     │                        │───────────────────►    │
     │                        │                        │  Show preview
     │                        │                        │  Confirm/Reject
     │  Poll status           │                        │
     │◄───────────────────    │  Print                 │
     │                        │◄───────────────────    │
```

## Project Structure

```
prime-print/
├── backend/           Python FastAPI server
│   ├── app/
│   │   ├── api/       REST endpoints
│   │   ├── processing/ Image processing pipeline
│   │   ├── profiles/  Document type configs
│   │   ├── ws/        WebSocket handlers
│   │   └── services/  Business logic
│   └── tests/         Unit tests
├── frontend/          Customer upload page (mobile-first)
├── agent/             Windows desktop agent
├── scripts/           Setup utilities
└── static/            Generated QR codes + previews
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload/{shop_id}` | Upload document images |
| GET | `/api/v1/jobs/{job_id}` | Get job status |
| PATCH | `/api/v1/jobs/{job_id}/documents/{doc_id}/confirm` | Confirm document |
| PATCH | `/api/v1/jobs/{job_id}/documents/{doc_id}/reject` | Reject document |
| GET | `/api/v1/shop/{shop_id}/pending` | Get pending jobs |
| POST | `/api/v1/shop` | Create shop |
| GET | `/api/v1/shop/{shop_id}` | Get shop info |

## Supported Documents

- Aadhaar Card
- PAN Card
- Voter ID

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Image Processing:** OpenCV, Pillow, Tesseract OCR
- **PDF:** img2pdf
- **Frontend:** Vanilla HTML/CSS/JS
- **Desktop Agent:** Python, websockets, pystray
