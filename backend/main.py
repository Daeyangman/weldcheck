import os
import uuid
import json
import sqlite3
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR.parent / "models"
UPLOADS_DIR = BASE_DIR / "uploads"
CROPS_DIR = BASE_DIR / "crops"
DB_PATH = BASE_DIR / "data" / "welding.db"

UPLOADS_DIR.mkdir(exist_ok=True)
CROPS_DIR.mkdir(exist_ok=True)
DB_PATH.parent.mkdir(exist_ok=True)

SECRET_KEY = "weldcheck-secret-key-2024"
ALGORITHM = "HS256"

WHITELIST_USERS = {
    "이상호": "a이상호",
    "윤재욱": "a윤재욱",
    "이한종": "a이한종",
    "하승구": "a하승구",
    "조재흥": "a조재흥",
}


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username


class LoginRequest(BaseModel):
    username: str
    password: str


# Cache loaded YOLO models
_model_cache: dict[str, YOLO] = {}


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            original_path TEXT NOT NULL,
            model_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            pass_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            bbox_x1 REAL, bbox_y1 REAL, bbox_x2 REAL, bbox_y2 REAL,
            crop_path TEXT NOT NULL,
            judgment TEXT NOT NULL,
            FOREIGN KEY (inspection_id) REFERENCES inspections(id)
        );
    """)
    conn.close()


def load_model(model_name: str) -> YOLO:
    if model_name not in _model_cache:
        model_path = MODELS_DIR / model_name
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        _model_cache[model_name] = YOLO(str(model_path))
    return _model_cache[model_name]


def judge_weld(class_name: str, confidence: float) -> str:
    """
    Determine PASS/FAIL for a detected weld.
    This is a placeholder logic - customize based on your fine-tuned model's classes.
    Classes containing keywords like 'good', 'normal', 'pass', 'ok' -> PASS
    Classes containing keywords like 'bad', 'defect', 'crack', 'fail', 'porosity', 'spatter', 'undercut' -> FAIL
    Default: if confidence > 0.5 -> PASS, else FAIL
    """
    name_lower = class_name.lower()
    fail_keywords = ['bad', 'defect', 'crack', 'fail', 'porosity', 'spatter', 'undercut', 'overlap', 'incomplete']
    pass_keywords = ['good', 'normal', 'pass', 'ok', 'acceptable']

    for kw in fail_keywords:
        if kw in name_lower:
            return "FAIL"
    for kw in pass_keywords:
        if kw in name_lower:
            return "PASS"

    return "PASS" if confidence > 0.5 else "FAIL"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="WeldCheck API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login")
def login(req: LoginRequest):
    if req.username not in WHITELIST_USERS:
        raise HTTPException(status_code=401, detail="허가되지 않은 사용자입니다")
    if WHITELIST_USERS[req.username] != req.password:
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다")
    token = create_token(req.username)
    return {"token": token, "username": req.username}


@app.get("/me")
def get_me(authorization: str = Header(None)):
    username = get_current_user(authorization)
    return {"username": username}


@app.get("/users")
def list_users():
    return list(WHITELIST_USERS.keys())


@app.get("/models")
def list_models():
    """List available YOLO model files in the models directory."""
    if not MODELS_DIR.exists():
        MODELS_DIR.mkdir(exist_ok=True)
        return []
    extensions = {'.pt', '.onnx', '.engine', '.torchscript'}
    models = [f.name for f in MODELS_DIR.iterdir() if f.suffix in extensions]
    return sorted(models)


@app.post("/inspect")
async def run_inspection(
    file: UploadFile = File(...),
    model: str = Form(...),
    authorization: str = Header(None)
):
    """Run YOLO inspection on uploaded image/video frame."""
    username = get_current_user(authorization)
    # Save uploaded file
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    file_id = str(uuid.uuid4())
    save_path = UPLOADS_DIR / f"{file_id}{ext}"

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Load model and run inference
    yolo_model = load_model(model)
    results = yolo_model(str(save_path))

    # Process detections
    detections = []
    pass_count = 0
    fail_count = 0

    from PIL import Image
    img = Image.open(save_path)

    for r in results:
        if r.boxes is None:
            continue
        for i, box in enumerate(r.boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = yolo_model.names.get(cls_id, str(cls_id))

            # Crop detection
            crop = img.crop((int(x1), int(y1), int(x2), int(y2)))
            crop_filename = f"{file_id}_crop_{i}.jpg"
            crop_path = CROPS_DIR / crop_filename
            crop.save(crop_path, "JPEG", quality=95)

            judgment = judge_weld(cls_name, conf)
            if judgment == "PASS":
                pass_count += 1
            else:
                fail_count += 1

            detections.append({
                "class_name": cls_name,
                "confidence": conf,
                "bbox": [x1, y1, x2, y2],
                "crop_path": str(crop_path.relative_to(BASE_DIR)),
                "judgment": judgment
            })

    # Save to database
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO inspections (user_name, original_filename, original_path, model_name, created_at, pass_count, fail_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, file.filename, str(save_path.relative_to(BASE_DIR)), model, datetime.now().isoformat(), pass_count, fail_count)
    )
    inspection_id = cursor.lastrowid

    for det in detections:
        conn.execute(
            "INSERT INTO detections (inspection_id, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, crop_path, judgment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (inspection_id, det["class_name"], det["confidence"],
             det["bbox"][0], det["bbox"][1], det["bbox"][2], det["bbox"][3],
             det["crop_path"], det["judgment"])
        )
    conn.commit()
    conn.close()

    return {
        "inspection_id": inspection_id,
        "model": model,
        "detections": detections,
        "pass_count": pass_count,
        "fail_count": fail_count
    }


@app.get("/history")
def get_history():
    """Get inspection history with detections."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM inspections ORDER BY created_at DESC LIMIT 100"
    ).fetchall()

    result = []
    for row in rows:
        record = dict(row)
        dets = conn.execute(
            "SELECT * FROM detections WHERE inspection_id = ?", (row["id"],)
        ).fetchall()
        record["detections"] = [dict(d) for d in dets]
        result.append(record)

    conn.close()
    return result


@app.get("/files/{file_path:path}")
def serve_file(file_path: str):
    """Serve uploaded images and crop files."""
    full_path = BASE_DIR / file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not full_path.resolve().is_relative_to(BASE_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    return FileResponse(full_path)
