# Runova Print — Implementation Plan v0.1

> **MVP Goal:** Customer uploads document photo → system auto-processes → shopkeeper confirms → print-ready PDF generated.

---

## 1. Project Structure

```
prime-print/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Environment variables, settings
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models.py            # ORM models (Shop, Job, Document)
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py        # POST /api/v1/upload/{shop_id}
│   │   │   ├── jobs.py          # GET/PATCH job endpoints
│   │   │   └── shop.py          # Shop registration + QR generation
│   │   ├── processing/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py      # Orchestrates full processing chain
│   │   │   ├── validator.py     # Image validation (type, size, quality)
│   │   │   ├── detector.py      # Document boundary detection
│   │   │   ├── perspective.py   # 4-point perspective correction
│   │   │   ├── enhancer.py      # Brightness, contrast, sharpness, denoise
│   │   │   ├── classifier.py    # Document type detection via OCR
│   │   │   ├── layout.py        # A4 canvas placement
│   │   │   └── pdf_gen.py       # PDF output generation
│   │   ├── profiles/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py        # Profile loader utility
│   │   │   ├── aadhaar.json     # Aadhaar Card profile
│   │   │   ├── pan.json         # PAN Card profile
│   │   │   └── voter_id.json    # Voter ID profile
│   │   ├── ws/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py    # WebSocket connection manager
│   │   │   └── agent.py         # Desktop agent WS endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── job_manager.py   # Job state machine logic
│   │       └── file_manager.py  # Temp file storage + cleanup
│   ├── uploads/                 # Raw uploaded images (temp)
│   ├── outputs/                 # Generated print-ready PDFs (temp)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   │   ├── test_upload.py
│   │   │   └── test_jobs.py
│   │   ├── test_processing/
│   │   │   ├── test_validator.py
│   │   │   ├── test_detector.py
│   │   │   ├── test_perspective.py
│   │   │   ├── test_enhancer.py
│   │   │   ├── test_classifier.py
│   │   │   └── test_layout.py
│   │   └── test_services/
│   │       └── test_job_manager.py
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── index.html               # Customer upload page (mobile-first)
│   ├── style.css                # Responsive styles
│   ├── app.js                   # Upload logic, camera, gallery
│   └── assets/
│       └── logo.svg
├── agent/
│   ├── runova_agent.py          # Desktop agent main entry
│   ├── websocket_client.py      # WebSocket connection to server
│   ├── printer.py               # Windows print integration
│   ├── tray.py                  # System tray icon + menu
│   ├── preview.py               # PDF preview window
│   ├── requirements.txt
│   └── build.bat                # PyInstaller build script
├── scripts/
│   ├── setup_db.py              # Initialize database tables
│   └── seed_shop.py             # Create a test shop + QR
├── static/
│   ├── qr/                      # Generated QR codes
│   └── previews/                # Processed document previews
├── IMPLEMENTATION.md            # This file
├── PRD.md
└── README.md
```

---

## 2. Database Schema (SQLite)

### Entity Relationship

```
Shop 1──* Job 1──* Document
```

### Tables

#### Shop

| Column     | Type    | Notes                      |
|------------|---------|----------------------------|
| shop_id    | UUID PK | Auto-generated             |
| shop_name  | TEXT    | Shop display name          |
| device_id  | TEXT    | Desktop agent device ID    |
| created_at | DATETIME| Default: now               |

#### Job

| Column       | Type    | Notes                          |
|--------------|---------|--------------------------------|
| job_id       | UUID PK | Auto-generated                 |
| shop_id      | UUID FK | References Shop.shop_id        |
| status       | TEXT    | State machine status           |
| created_at   | DATETIME| Default: now                   |
| completed_at | DATETIME| Null until completed/failed    |

#### Document

| Column        | Type    | Notes                            |
|---------------|---------|----------------------------------|
| document_id   | UUID PK | Auto-generated                   |
| job_id        | UUID FK | References Job.job_id            |
| document_type | TEXT    | aadhaar / pan / voter_id / unknown |
| input_path    | TEXT    | Path to uploaded image           |
| output_path   | TEXT    | Path to processed PDF            |
| preview_path  | TEXT    | Path to preview image            |
| status        | TEXT    | Document-level state             |
| error_message | TEXT    | Null unless failed               |
| created_at    | DATETIME| Default: now                     |

---

## 3. Job State Machine

```
                    ┌──────────┐
                    │ UPLOADED │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │VALIDATING│
                    └────┬─────┘
                         │
                    ┌────▼──────┐
              ┌────►│PROCESSING │◄────┐
              │     └────┬──────┘     │
              │          │            │
              │    ┌─────▼────┐       │
              │    │  READY   │       │
              │    └────┬─────┘       │
              │         │             │
              │    ┌────▼─────┐       │
              │    │ PREVIEW  │       │
              │    └────┬─────┘       │
              │         │             │
              │    ┌────▼──────┐      │
              │    │ CONFIRMED │      │
              │    └────┬──────┘      │
              │         │             │
              │    ┌────▼─────┐       │
              │    │PRINTING  │       │
              │    └────┬─────┘       │
              │         │             │
              │    ┌────▼─────┐       │
              │    │COMPLETED │       │
              │    └──────────┘       │
              │                       │
              │    ┌──────────┐       │
              └────┤  FAILED  │───────┘
                   └────┬─────┘  (retry)
                        │
                   ┌────▼──────────┐
                   │ MANUAL_REVIEW │
                   └───────────────┘
```

### State Transitions

| Current State   | Trigger              | Next State     |
|-----------------|----------------------|----------------|
| UPLOADED        | Validation start     | VALIDATING     |
| VALIDATING      | Validation pass      | PROCESSING     |
| VALIDATING      | Validation fail      | FAILED         |
| PROCESSING      | Pipeline complete    | READY          |
| PROCESSING      | Pipeline error       | FAILED         |
| READY           | Agent requests       | PREVIEW        |
| PREVIEW         | Shopkeeper confirms  | CONFIRMED      |
| PREVIEW         | Shopkeeper rejects   | FAILED         |
| CONFIRMED       | Print command        | PRINTING       |
| PRINTING        | Print success        | COMPLETED      |
| PRINTING        | Print failure        | FAILED         |
| FAILED          | Retry                | UPLOADED       |
| FAILED          | Manual fix           | MANUAL_REVIEW  |

---

## 4. API Design

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

#### Upload

```
POST /upload/{shop_id}
Content-Type: multipart/form-data

Body:
  files: List[UploadFile]   # One or more images

Response 201:
{
  "job_id": "uuid",
  "shop_id": "uuid",
  "status": "UPLOADED",
  "documents": [
    {
      "document_id": "uuid",
      "filename": "aadhaar_front.jpg",
      "status": "UPLOADED"
    }
  ]
}
```

#### Job Status

```
GET /jobs/{job_id}

Response 200:
{
  "job_id": "uuid",
  "shop_id": "uuid",
  "status": "PROCESSING",
  "documents": [
    {
      "document_id": "uuid",
      "document_type": "aadhaar",
      "status": "READY",
      "preview_url": "/static/previews/{document_id}.jpg"
    }
  ],
  "created_at": "2026-08-23T10:00:00Z",
  "completed_at": null
}
```

#### Confirm Document

```
PATCH /jobs/{job_id}/documents/{document_id}/confirm

Response 200:
{
  "document_id": "uuid",
  "status": "CONFIRMED"
}
```

#### Reject Document

```
PATCH /jobs/{job_id}/documents/{document_id}/reject

Response 200:
{
  "document_id": "uuid",
  "status": "FAILED",
  "message": "Rejected by shopkeeper"
}
```

#### Get Pending Jobs (for Desktop Agent)

```
GET /shop/{shop_id}/pending

Response 200:
{
  "jobs": [
    {
      "job_id": "uuid",
      "status": "READY",
      "document_count": 3,
      "created_at": "2026-08-23T10:05:00Z"
    }
  ]
}
```

#### Download Processed PDF

```
GET /documents/{document_id}/pdf

Response 200:
  Binary PDF file
```

#### WebSocket (Desktop Agent)

```
ws://localhost:8000/ws/agent/{device_id}

Server → Agent messages:
  {
    "type": "new_job",
    "job_id": "uuid",
    "shop_id": "uuid",
    "document_count": 3
  }

  {
    "type": "job_updated",
    "job_id": "uuid",
    "document_id": "uuid",
    "status": "CONFIRMED"
  }

Agent → Server messages:
  {
    "type": "agent_ready",
    "device_id": "uuid"
  }

  {
    "type": "print_complete",
    "document_id": "uuid",
    "success": true
  }

  {
    "type": "print_failed",
    "document_id": "uuid",
    "error": "Printer offline"
  }
```

---

## 5. Processing Pipeline

### Pipeline Flow

```python
def process_document(input_path: str, output_dir: str) -> dict:
    """
    Full document processing pipeline.
    Returns: { output_path, preview_path, document_type, confidence }
    """

    # Step 1: Validate image
    validated = validator.validate(input_path)

    # Step 2: Detect document boundary
    contour = detector.detect_document(validated)

    # Step 3: Perspective correction
    warped = perspective.correct(validated, contour)

    # Step 4: Auto crop
    cropped = detector.crop_to_document(warped, contour)

    # Step 5: Enhance for print
    enhanced = enhancer.optimize_for_print(cropped)

    # Step 6: Classify document type
    doc_type, confidence = classifier.classify(enhanced)

    # Step 7: Load document profile
    profile = loader.load(doc_type)

    # Step 8: Place on A4 layout
    a4_page = layout.place_on_a4(enhanced, profile)

    # Step 9: Generate PDF
    pdf_path = pdf_gen.generate(a4_page, output_dir)

    # Step 10: Generate preview thumbnail
    preview_path = generate_preview(a4_page, output_dir)

    return {
        "output_path": pdf_path,
        "preview_path": preview_path,
        "document_type": doc_type,
        "confidence": confidence
    }
```

### Step Details

#### 5.1 Image Validation (`validator.py`)

```python
Checks:
  - File extension in ALLOWED_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
  - File size <= MAX_FILE_SIZE (20 MB)
  - Image readable by Pillow (not corrupted)
  - Minimum resolution >= 600x800 px
  - EXIF orientation correction
```

#### 5.2 Document Boundary Detection (`detector.py`)

```python
Algorithm:
  1. Convert to grayscale
  2. Gaussian blur (kernel 5x5)
  3. Canny edge detection (auto-threshold)
  4. Find contours
  5. Filter contours by area (>10% of image area)
  6. Approximate contour to polygon
  7. Find 4-sided polygon with largest area
  8. Order points: top-left, top-right, bottom-right, bottom-left
  9. Return 4 corner points

Fallback: If no 4-sided contour found, use full image (no crop)
```

#### 5.3 Perspective Correction (`perspective.py`)

```python
Algorithm:
  1. Receive 4 corner points from detector
  2. Calculate target rectangle dimensions:
     - width = max(dist(top-left, top-right), dist(bottom-left, bottom-right))
     - height = max(dist(top-left, bottom-left), dist(top-right, bottom-right))
  3. Build source points array (4 corners)
  4. Build destination points array (rectangle)
  5. cv2.getPerspectiveTransform(src, dst)
  6. cv2.warpPerspective(image, M, (width, height))
  7. Return corrected image
```

#### 5.4 Image Enhancement (`enhancer.py`)

```python
Processing chain:
  1. Convert to grayscale (for documents)
  2. Adaptive histogram equalization (CLAHE)
  3. Denoise: cv2.fastNlMeansDenoising(h=10)
  4. Sharpen: unsharp mask kernel
  5. Brightness/contrast auto-adjust:
     - Calculate mean brightness
     - If too dark: increase brightness
     - If too bright: decrease brightness
     - Normalize contrast
  6. Binarize (optional): Otsu's threshold for pure B&W documents
  7. White background correction:
     - Detect background color
     - Normalize to pure white
```

#### 5.5 Document Type Classifier (`classifier.py`)

```python
MVP Strategy: OCR + keyword matching

  1. Run Tesseract OCR on enhanced image
  2. Extract text blocks
  3. Match against known patterns:

     Aadhaar:
       - Contains "भारत सरकार" or "Government of India"
       - Contains "आधार" or "AADHAAR"
       - Contains 12-digit number pattern

     PAN Card:
       - Contains "INCOME TAX DEPARTMENT"
       - Contains "Permanent Account Number"
       - Contains 10-digit alphanumeric PAN format

     Voter ID:
       - Contains "ELECTION COMMISSION OF INDIA"
       - Contains "Voter ID" or "मतदाता पहचान"
       - Contains EPIC number pattern

  4. Score each profile
  5. Return highest scoring match (if confidence > threshold)
  6. Return "unknown" if no match above threshold
```

#### 5.6 A4 Layout (`layout.py`)

```python
A4 Dimensions (300 DPI):
  - Width:  2480 px  (210mm)
  - Height: 3508 px  (297mm)

Algorithm:
  1. Create white A4 canvas (2480 x 3508, RGB)
  2. Load document profile (target size, margins)
  3. Scale processed document to fit within profile dimensions
     - Maintain aspect ratio
     - Fit within target_width - (2 * margin)
     - Fit within target_height - (2 * margin)
  4. Calculate centered position
  5. Paste document onto canvas
  6. Return final A4 image
```

#### 5.7 PDF Generation (`pdf_gen.py`)

```python
Using img2pdf (lossless JPEG→PDF) or Pillow:

  1. Take A4 image (PNG or JPEG)
  2. Set page size to A4 (210mm x 297mm)
  3. Embed image at full resolution
  4. Save as PDF
  5. Return file path

Output: {output_dir}/{document_id}.pdf
```

---

## 6. Document Profiles

### aadhaar.json

```json
{
  "document_name": "Aadhaar Card",
  "document_id": "aadhaar",
  "detection_rules": {
    "keywords": ["आधार", "AADHAAR", "भारत सरकार", "Government of India"],
    "id_pattern": "\\d{4}\\s\\d{4}\\s\\d{4}",
    "geometry": {
      "expected_aspect_ratio": 1.586,
      "tolerance": 0.15
    }
  },
  "target_width_mm": 85.6,
  "target_height_mm": 54.0,
  "target_width_px": 1063,
  "target_height_px": 674,
  "aspect_ratio": 1.586,
  "margin_mm": 3.0,
  "margin_px": 37,
  "color_mode": "grayscale",
  "print_configuration": {
    "orientation": "landscape",
    "duplex": false,
    "copies": 1
  }
}
```

### pan.json

```json
{
  "document_name": "PAN Card",
  "document_id": "pan",
  "detection_rules": {
    "keywords": ["INCOME TAX DEPARTMENT", "Permanent Account Number", "पैन"],
    "id_pattern": "[A-Z]{5}\\d{4}[A-Z]",
    "geometry": {
      "expected_aspect_ratio": 1.586,
      "tolerance": 0.15
    }
  },
  "target_width_mm": 85.6,
  "target_height_mm": 54.0,
  "target_width_px": 1063,
  "target_height_px": 674,
  "aspect_ratio": 1.586,
  "margin_mm": 3.0,
  "margin_px": 37,
  "color_mode": "grayscale",
  "print_configuration": {
    "orientation": "landscape",
    "duplex": false,
    "copies": 1
  }
}
```

### voter_id.json

```json
{
  "document_name": "Voter ID",
  "document_id": "voter_id",
  "detection_rules": {
    "keywords": ["ELECTION COMMISSION OF INDIA", "Voter ID", "मतदाता पहचान", "EPIC"],
    "id_pattern": "[A-Z]{3}\\d{7}",
    "geometry": {
      "expected_aspect_ratio": 1.586,
      "tolerance": 0.15
    }
  },
  "target_width_mm": 85.6,
  "target_height_mm": 54.0,
  "target_width_px": 1063,
  "target_height_px": 674,
  "aspect_ratio": 1.586,
  "margin_mm": 3.0,
  "margin_px": 37,
  "color_mode": "grayscale",
  "print_configuration": {
    "orientation": "landscape",
    "duplex": false,
    "copies": 1
  }
}
```

---

## 7. Frontend — Customer Upload Page

### Tech

- Vanilla HTML/CSS/JS (no build tools)
- Mobile-first responsive design
- Uses `fetch()` API for uploads

### Page Flow

```
Landing Page
    │
    ├── [Take Photo] → Opens camera (input capture="environment")
    ├── [Choose from Gallery] → File picker (input multiple)
    │
    ├── Selected Images List (thumbnails)
    │     ├── Image 1  [x]
    │     └── Image 2  [x]
    │
    └── [SEND DOCUMENT] → Upload all images
          │
          ├── Progress bar (per file)
          ├── Status: "Uploading..." → "Processing..." → "Done!"
          └── Confirmation screen
```

### Key Elements

```html
<!-- Camera capture -->
<input type="file" accept="image/*" capture="environment" id="camera" multiple>

<!-- Gallery selection -->
<input type="file" accept="image/*" id="gallery" multiple>

<!-- Upload progress -->
<div class="progress-bar">
  <div class="progress-fill" style="width: 0%"></div>
</div>

<!-- Status display -->
<div id="status">Ready to upload</div>
```

### Responsive Breakpoints

```css
/* Mobile: full width, large touch targets */
@media (max-width: 480px) {
  button { min-height: 56px; font-size: 18px; }
}

/* Tablet: centered layout */
@media (min-width: 481px) and (max-width: 768px) {
  .container { max-width: 480px; margin: 0 auto; }
}
```

---

## 8. Desktop Agent

### Tech Stack

- Python 3.10+
- `websockets` — WebSocket client
- `Pillow` — PDF preview rendering
- `pystray` — System tray icon
- `win32print` — Windows print integration
- `PyInstaller` — Build to .exe

### Agent Lifecycle

```
Start
  │
  ├── Load config (device_id, server_url)
  ├── Connect to WebSocket
  ├── Register as ready
  │
  ├── Listen for messages
  │     │
  │     ├── new_job → Show notification
  │     │              → Download PDF
  │     │              → Show preview window
  │     │              → Show confirm/reject buttons
  │     │
  │     ├── job_updated → Update status display
  │     │
  │     └── disconnected → Auto-reconnect (exponential backoff)
  │
  ├── On confirm → Send confirm to server → Trigger print
  ├── On reject → Send reject to server
  │
  └── On exit → Disconnect WebSocket → Close tray
```

### Preview Window

```
┌────────────────────────────────┐
│  Runova Print Agent            │
│                                │
│  Document Ready                │
│  Type: Aadhaar Card            │
│  Job: #a3f2b1c                 │
│                                │
│  ┌──────────────────────────┐  │
│  │                          │  │
│  │     [PDF PREVIEW]        │  │
│  │     (rendered page)      │  │
│  │                          │  │
│  └──────────────────────────┘  │
│                                │
│  [ PRINT ]  [ REJECT ]         │
│                                │
└────────────────────────────────┘
```

### Print Integration

```python
import win32print
import win32api

def print_pdf(pdf_path: str, printer_name: str = None):
    """Send PDF to Windows printer."""
    if printer_name is None:
        printer_name = win32print.GetDefaultPrinter()

    # Use SumatraPDF or similar for command-line PDF printing
    # Or use win32api.ShellExecute for default PDF viewer print
    win32api.ShellExecute(
        0, "print", pdf_path,
        f'/d "{printer_name}"', ".", 0
    )
```

---

## 9. Security & Privacy

### Principles

| Measure                | Implementation                                    |
|------------------------|---------------------------------------------------|
| HTTPS                  | Use reverse proxy (nginx/caddy) in production     |
| Random job IDs         | UUID4 for all IDs, no sequential numbering        |
| Access-controlled files | Serve files only via authenticated API endpoints  |
| No public URLs         | All document access requires job_id + document_id |
| Auto-deletion          | Cron job deletes files older than 1 hour          |
| Minimal logging        | Log job IDs only, never log document content      |
| Secure upload          | Validate file types server-side, scan for malware |

### Auto-Cleanup

```python
# Background task runs every 10 minutes
async def cleanup_old_files():
    """Delete uploads and outputs older than 1 hour."""
    cutoff = datetime.now() - timedelta(hours=1)

    # Delete old upload files
    for path in Path("uploads").glob("*"):
        if path.stat().st_mtime < cutoff.timestamp():
            path.unlink(missing_ok=True)

    # Delete old output files
    for path in Path("outputs").glob("*"):
        if path.stat().st_mtime < cutoff.timestamp():
            path.unlink(missing_ok=True)
```

---

## 10. Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "DOCUMENT_NOT_DETECTED",
    "message": "Could not detect document boundary in the image.",
    "suggestion": "Please take a clearer photo with good lighting.",
    "retryable": true
  }
}
```

### Error Codes

| Code                   | HTTP Status | Retryable | Description                        |
|------------------------|-------------|-----------|------------------------------------|
| INVALID_FILE_TYPE      | 400         | No        | Unsupported file format            |
| FILE_TOO_LARGE         | 400         | No        | File exceeds 20MB limit            |
| IMAGE_CORRUPTED        | 400         | No        | File is not a valid image          |
| IMAGE_TOO_SMALL        | 400         | No        | Resolution below minimum threshold |
| DOCUMENT_NOT_DETECTED  | 422         | Yes       | Boundary detection failed          |
| LOW_IMAGE_QUALITY      | 422         | Yes       | Image too blurry/dark              |
| UNKNOWN_DOCUMENT_TYPE  | 422         | No        | OCR could not classify document    |
| PROCESSING_FAILED      | 500         | Yes       | Internal processing error          |
| PRINTER_OFFLINE        | 503         | Yes       | Desktop printer not available      |
| JOB_NOT_FOUND          | 404         | No        | Job ID does not exist              |

---

## 11. Dependencies

### Backend (`requirements.txt`)

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy==2.0.36
aiosqlite==0.20.0
python-multipart==0.0.18
python-dotenv==1.0.1
pydantic==2.10.0
opencv-python-headless==4.10.0.84
Pillow==11.0.0
pytesseract==0.3.13
img2pdf==0.5.1
websockets==14.2
qrcode[pil]==8.0
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.25.0
```

### Agent (`requirements.txt`)

```
websockets==14.2
Pillow==11.0.0
pystray==0.19.5
pywin32==308
PyInstaller==6.11.1
```

---

## 12. Build & Run

### Backend

```bash
cd backend

# Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Initialize database
python scripts/setup_db.py

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Serve with any static server
python -m http.server 3000

# Or serve from FastAPI (included in backend)
```

### Desktop Agent

```bash
cd agent

# Setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run
python runova_agent.py

# Build to .exe
pyinstaller --onefile --windowed runova_agent.py
```

---

## 13. Development Phases & Timeline

### Phase 1: Foundation (Days 1-2)

- [x] Project scaffold and directory structure
- [ ] Python virtual environment + dependencies
- [ ] SQLAlchemy models (Shop, Job, Document)
- [ ] Database initialization script
- [ ] Config management (.env)
- [ ] Basic FastAPI app skeleton

### Phase 2: Processing Engine (Days 3-5)

- [ ] Image validator (type, size, corruption, resolution)
- [ ] Document boundary detector (OpenCV contour)
- [ ] Perspective correction (4-point transform)
- [ ] Auto cropping
- [ ] Image enhancement (brightness, contrast, denoise, sharpen)
- [ ] Document classifier (Tesseract + keyword matching)
- [ ] Document profiles (JSON loader)
- [ ] A4 layout engine
- [ ] PDF generation
- [ ] Unit tests for each module

### Phase 3: API Layer (Days 5-6)

- [ ] Upload endpoint (multi-file, progress tracking)
- [ ] Job status endpoint
- [ ] Document confirm/reject endpoints
- [ ] Shop pending jobs endpoint
- [ ] PDF download endpoint
- [ ] Error handling middleware
- [ ] Static file serving
- [ ] WebSocket endpoint for desktop agent
- [ ] API tests

### Phase 4: Customer Frontend (Day 7)

- [ ] Mobile-first upload page
- [ ] Camera capture integration
- [ ] Gallery selection
- [ ] Multi-image preview
- [ ] Upload progress bar
- [ ] Processing status display
- [ ] Confirmation screen
- [ ] QR code generation per shop

### Phase 5: Desktop Agent (Days 8-9)

- [ ] WebSocket client with auto-reconnect
- [ ] System tray icon
- [ ] Job notification popup
- [ ] PDF preview window
- [ ] Confirm/reject buttons
- [ ] Windows print integration
- [ ] Build script for .exe

### Phase 6: Polish & Testing (Day 10)

- [ ] End-to-end workflow test
- [ ] Error scenario testing
- [ ] Auto-cleanup implementation
- [ ] Security audit
- [ ] Performance testing with large images
- [ ] README with setup instructions

---

## 14. Future Enhancements (Post-MVP)

### V0.2

- Manual crop editor (interactive canvas)
- Image quality scoring
- Better OCR accuracy
- Retry with different parameters

### V0.3

- AI document classifier (ML model)
- Smart layout optimization (fit multiple docs on one page)
- Print queue management
- Copy count selection

### V1.0

- Multi-shop support with cloud dashboard
- Shop analytics and reporting
- Printer management
- User accounts and authentication
- Shop-specific QR codes
- Multiple PC/printer support
