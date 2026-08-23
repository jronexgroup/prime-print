# Runova Print — PRD v0.1

## 1. Product Overview

**Runova Print** is a document-processing and printing automation system designed for photocopy/printing shops.

The system eliminates repetitive manual work such as:

* Downloading customer documents from WhatsApp
* Opening images in Paint
* Converting image formats
* Manually cropping documents
* Adjusting brightness/contrast
* Manually resizing documents
* Placing documents on an A4 white background
* Opening Photoshop
* Preparing print layouts
* Repeating the same workflow for multiple documents

### Core Product Promise

> **Customer uploads → Runova processes → Shopkeeper confirms → Print.**

---

# 2. Problem Statement

Currently, customers often forget to bring physical copies of documents such as:

* Aadhaar Card
* PAN Card
* Voter ID
* Other identity/document images

They send photographs through WhatsApp.

The shopkeeper then has to manually:

```text
WhatsApp
   ↓
Download image
   ↓
Desktop
   ↓
Paint
   ↓
Save/convert
   ↓
Photoshop 7.0
   ↓
Crop
   ↓
Resize
   ↓
Adjust brightness/contrast
   ↓
Place on A4
   ↓
Print
```

This process is slow, repetitive and error-prone.

---

# 3. Proposed Solution

Runova Print replaces the manual workflow with a dedicated document-upload and print-preparation pipeline.

### Customer Flow

```text
Scan QR
   ↓
Open Runova Print Upload Page
   ↓
Upload / Capture Document
   ↓
Submit
```

### Runova Processing

```text
Receive Image
   ↓
Validate
   ↓
Detect Document
   ↓
Crop
   ↓
Perspective Correction
   ↓
Enhancement
   ↓
Document Type Detection
   ↓
Apply Document Profile
   ↓
A4 Layout
   ↓
Generate Print-Ready PDF
```

### Shopkeeper Flow

```text
New Document Notification
        ↓
Print Preview
        ↓
Confirm / Reject
        ↓
Print
```

---

# 4. Target Users

## Primary User

### Photocopy / Printing Shop Owner

Needs:

* Fast processing
* Minimal interaction
* Reliable document sizing
* Easy print preview
* Simple confirmation workflow

## Secondary User

### Customer

Needs:

* Simple upload
* No account creation
* Mobile-friendly interface
* Quick submission
* Clear upload status

---

# 5. Core Features

## 5.1 QR Upload System

Each shop has a unique QR code.

Customer scans QR code.

Example:

```text
┌────────────────────┐
│                    │
│     RUNOVA PRINT   │
│                    │
│      [ QR ]        │
│                    │
│ Scan to Send       │
│ Your Document      │
└────────────────────┘
```

QR opens the shop's upload page.

---

# 6. Customer Upload Interface

The interface should be extremely simple.

### Required UI

* Upload image
* Camera capture
* Gallery selection
* Multiple image selection
* Upload progress
* Processing status
* Submission confirmation

Example:

```text
Runova Print

Upload your document

[ 📷 Take Photo ]

[ 🖼️ Choose from Gallery ]

Selected:
✓ Image 1
✓ Image 2

[ SEND DOCUMENT ]
```

No customer account should be required in MVP.

---

# 7. Image Processing Engine

The processing engine is the core of Runova Print.

## 7.1 Image Validation

Check:

* File type
* File size
* Resolution
* Corrupted image
* Orientation

Unsupported/invalid images should be rejected.

---

# 8. Document Boundary Detection

The system should detect the physical document inside the photograph.

Example:

```text
Original Image

┌─────────────────────────────┐
│                             │
│      ┌───────────────┐      │
│      │               │      │
│      │   DOCUMENT    │      │
│      │               │      │
│      └───────────────┘      │
│                             │
└─────────────────────────────┘
```

System identifies the document boundary.

---

# 9. Perspective Correction

If the customer photographs the document at an angle, Runova should correct the perspective.

```text
Before

   /─────────/
  /         /
 /─────────/

        ↓

After

┌───────────┐
│           │
│ DOCUMENT  │
│           │
└───────────┘
```

Primary technology:

**OpenCV**

---

# 10. Automatic Cropping

Remove unnecessary surroundings.

Input:

```text
Document + Table + Wall + Shadows
```

Output:

```text
Document only
```

---

# 11. Image Enhancement

Runova should automatically optimize the document for photocopying.

Possible processing:

* Brightness adjustment
* Contrast adjustment
* Sharpness
* Noise reduction
* White-background correction
* Grayscale optimization

The system should prioritize **print readability**, not photographic appearance.

---

# 12. Document Type Detection

Runova should identify document types.

Initial supported documents:

1. Aadhaar Card
2. PAN Card
3. Voter ID

Future:

* Driving Licence
* Passport
* School ID
* Certificates
* Other documents

### Detection Strategy

MVP:

```text
OCR
+
Text matching
+
Pattern detection
+
Document geometry
```

Future:

```text
AI/ML classifier
```

---

# 13. Document Profiles

Each document type should have a configurable profile.

Example:

```text
DocumentProfile
│
├── document_name
├── detection_rules
├── target_width
├── target_height
├── aspect_ratio
├── margin
├── color_mode
└── print_configuration
```

This prevents document-specific rules from being scattered throughout the application.

---

# 14. A4 Layout Engine

Processed documents are placed on a standard white A4 canvas.

Example:

```text
┌────────────────────────┐
│                        │
│     ┌────────────┐     │
│     │            │     │
│     │ DOCUMENT   │     │
│     │            │     │
│     └────────────┘     │
│                        │
└────────────────────────┘
```

The system should maintain the required physical dimensions.

Output should be **print-ready PDF**.

---

# 15. Multiple Documents

Customers can upload multiple documents.

Example:

```text
Aadhaar Front
Aadhaar Back
PAN
Voter ID
```

Backend may process documents in parallel.

However, shopkeeper confirmation should remain sequential.

```text
Document 1/4
Aadhaar Front

[ PREVIEW ]

[ ✓ CONFIRM ] [ ✕ REJECT ]
```

After confirmation:

```text
Document 2/4
Aadhaar Back
```

At the end:

```text
4 Documents Ready

[ PRINT ALL ]
```

---

# 16. Desktop Agent

A lightweight Windows application will run on the shopkeeper's PC.

### Name

**Runova Print Agent**

The agent runs in the background.

Responsibilities:

* Maintain server connection
* Receive new jobs
* Download print-ready files
* Show notification
* Open print preview
* Send confirmation
* Trigger Windows printing
* Report print status

---

# 17. Desktop Popup

When a document is ready:

```text
┌──────────────────────────────┐
│      Runova Print             │
│                              │
│  🆕 Document Ready           │
│                              │
│  Type: Aadhaar Card          │
│  Status: Ready               │
│                              │
│  [ PRINT PREVIEW ]           │
│                              │
│  [ ✓ CONFIRM ]  [ ✕ REJECT ] │
└──────────────────────────────┘
```

---

# 18. Server ↔ Desktop Communication

Primary communication:

**WebSocket**

Architecture:

```text
Customer
   │
   ▼
FastAPI Server
   │
   │ WebSocket
   ▼
Runova Print Agent
   │
   ▼
Windows Printer
```

Each shop/device receives jobs associated with its unique shop/device ID.

---

# 19. Backend

### Technology

**Python + FastAPI**

Responsibilities:

* Customer upload API
* Job management
* Processing pipeline
* Document classification
* PDF generation
* Desktop-agent communication
* Job status management
* Temporary file management

---

# 20. Initial Database

MVP can use:

**SQLite**

Example entities:

### Shop

```text
shop_id
shop_name
device_id
created_at
```

### Job

```text
job_id
shop_id
status
created_at
completed_at
```

### Document

```text
document_id
job_id
document_type
input_path
output_path
status
```

---

# 21. Job State Machine

Every document should have a clear state.

```text
UPLOADED
   ↓
VALIDATING
   ↓
PROCESSING
   ↓
READY
   ↓
PREVIEW
   ↓
CONFIRMED
   ↓
PRINTING
   ↓
COMPLETED
```

Failure:

```text
PROCESSING
    ↓
FAILED
    ↓
MANUAL REVIEW
```

---

# 22. Privacy & Data Retention

Documents such as Aadhaar and PAN contain sensitive personal information.

Therefore Runova should use **temporary document storage**.

Ideal flow:

```text
Upload
 ↓
Process
 ↓
Print
 ↓
Delete
```

MVP should avoid permanently storing customer documents unless explicitly required.

Required security measures:

* HTTPS
* Secure upload
* Random job IDs
* Access-controlled files
* Automatic deletion
* No public document URLs
* Minimal logging of personal information

---

# 23. Error Handling

Runova must not blindly print a bad result.

Possible errors:

### Document not detected

```text
⚠ Document could not be detected.

[ RETRY ]
[ MANUAL CROP ]
```

### Low image quality

```text
⚠ Image quality is too low.

Please upload a clearer photo.
```

### Unknown document

```text
⚠ Document type not recognized.

[ SELECT TYPE ]
```

### Processing failure

```text
⚠ Processing failed.

[ RETRY ]
[ MANUAL PROCESS ]
```

---

# 24. Manual Override

Automation should never completely remove human control.

Shopkeeper should be able to:

* Re-crop
* Rotate
* Adjust brightness
* Adjust contrast
* Select document type
* Change size
* Reject document
* Reprocess

The goal is:

> **Automation first, manual override when needed.**

---

# 25. MVP Scope

### Version 0.1

Focus only on the core workflow.

**Customer**

* QR
* Mobile upload
* Multiple images
* Upload status

**Backend**

* FastAPI
* Image processing
* OpenCV
* Basic OCR
* Document classification
* A4 generation
* PDF output

**Desktop**

* Windows agent
* Job notification
* Preview
* Confirm
* Print

**Documents**

* Aadhaar
* PAN
* Voter ID

---

# 26. Future Features

Potential future versions:

### V0.2

* Better document detection
* Automatic quality scoring
* Manual crop editor
* Better OCR

### V0.3

* AI document classifier
* Smart layout optimization
* Multiple copies
* Print queue

### V1.0

* Multi-shop support
* Cloud dashboard
* Shop analytics
* Printer management
* User accounts
* Shop-specific QR
* Multiple PCs/printers

### Future AI

```text
AI Document Understanding
        ↓
Document Type
        ↓
Layout Recommendation
        ↓
Quality Assessment
        ↓
Smart Enhancement
```

---

# 27. Success Metrics

The primary metric should be:

### **Time saved per document**

Current workflow:

> WhatsApp → Paint → Photoshop → Resize → Layout → Print

Target:

> Upload → Confirm → Print

Other metrics:

* Processing success rate
* Document detection accuracy
* Classification accuracy
* Average processing time
* Manual intervention rate
* Print failure rate

---

# 28. Product Philosophy

Runova Print should follow three principles:

### 1. Simple

Customer should understand the upload process immediately.

### 2. Automatic

Shopkeeper should not need Photoshop for routine documents.

### 3. Human-controlled

The system must always allow the shopkeeper to review before printing.

---

# 29. One-Line Product Definition

> **Runova Print is an automated document-to-print pipeline that turns a customer's mobile document photo into a verified, print-ready A4 document with minimal shopkeeper interaction.**

**PRD status: `DRAFT v0.1`**
**Next:** UI/UX flow → exact processing algorithm → API design → database schema → project folder structure → MVP development plan.
