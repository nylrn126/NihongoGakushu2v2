from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from fastapi import APIRouter, Cookie, Depends, FastAPI, HTTPException, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from seed_data.loader import ALL_CHAPTERS, chapter_summary
from quiz_generator import generate_extra_bunpo_questions

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
JWT_ALGORITHM = "HS256"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

app = FastAPI(title="Gakushu Nihongo API")
api = APIRouter(prefix="/api")
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gakushu")


# ---------- Pydantic ----------
class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=80)

class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8, max_length=128)

class QuizSubmission(BaseModel):
    quiz_kind: str = Field(default="bunpo")  # "bunpo" | "susun"
    answers: dict[str, Any]
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ProgressUpdate(BaseModel):
    chapter_number: int
    section: str = "bunpo"  # bunpo|kotoba|kanji|kaiwa|quiz|flashcard
    completed: bool = False
    resume_position: int = 0

class EmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)

class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    title_translation: Optional[str] = None
    content: Optional[dict] = None
    published: Optional[bool] = None


# ---------- Helpers ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def token_secret() -> str:
    return os.environ["JWT_SECRET"]

def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "learner"),
        "must_change_password": user.get("must_change_password", False),
    }

def public_attempt(attempt: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in attempt.items() if k not in {"_id", "user_id", "raw_answers"}}

def make_token(user_id: str, token_type: str, expiry: timedelta, jti: Optional[str] = None) -> str:
    return jwt.encode(
        {"sub": user_id, "type": token_type, "jti": jti or str(uuid.uuid4()),
         "exp": datetime.now(timezone.utc) + expiry},
        token_secret(), algorithm=JWT_ALGORITHM,
    )

def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, token_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(401, "Invalid session token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid session token")

def set_session(response: Response, user_id: str, refresh_jti: Optional[str] = None):
    refresh_jti = refresh_jti or str(uuid.uuid4())
    access = make_token(user_id, "access", timedelta(minutes=15))
    refresh = make_token(user_id, "refresh", timedelta(days=7), refresh_jti)
    response.set_cookie("access_token", access, httponly=True, secure=COOKIE_SECURE,
                        samesite="lax", max_age=900, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=COOKIE_SECURE,
                        samesite="lax", max_age=604800, path="/")
    return refresh_jti

async def current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get("access_token")
    if not token and request.headers.get("Authorization", "").startswith("Bearer "):
        token = request.headers["Authorization"][7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(token, "access")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(401, "User not found")
    return user

async def learner(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return user

async def admin_only(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return user


# ---------- Seeding ----------
async def seed_chapters():
    """Insert Minna chapters from bundled DSL if collection is empty."""
    if await db.chapters.count_documents({}) > 0:
        return
    docs = []
    now = datetime.now(timezone.utc).isoformat()
    for ch in ALL_CHAPTERS:
        doc = {
            "number": ch["number"],
            "book": ch["book"],
            "book_label": f"Minna no Nihongo {ch['book']}",
            "title": ch["title"],
            "title_translation": ch["title_translation"],
            "has_content": ch.get("has_content", True),
            "content": ch["content"],
            "published": True,
            "quiz_padded": False,
            "created_at": now,
            "updated_at": now,
        }
        docs.append(doc)
    if docs:
        await db.chapters.insert_many(docs)
        log.info("Seeded %d chapters", len(docs))


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.sessions.create_index("jti", unique=True)
    await db.progress.create_index([("user_id", 1), ("chapter_number", 1), ("section", 1)], unique=True)
    await db.attempts.create_index([("user_id", 1), ("operation_id", 1)], unique=True)
    await db.login_attempts.create_index("identifier", unique=True)
    await db.users.create_index("reset_expires_at", expireAfterSeconds=0)
    await db.chapters.create_index("number", unique=True)
    await seed_chapters()
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if admin_email and admin_password:
        existing = await db.users.find_one({"email": admin_email.lower()}, {"_id": 0})
        if not existing:
            await db.users.insert_one({
                "id": str(uuid.uuid4()), "email": admin_email.lower(),
                "name": "Editor", "password_hash": hash_password(admin_password),
                "role": "admin", "must_change_password": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        else:
            update = {"role": "admin"}
            if not verify_password(admin_password, existing["password_hash"]):
                update["password_hash"] = hash_password(admin_password)
                update["must_change_password"] = False
            await db.users.update_one({"id": existing["id"]}, {"$set": update})


@api.get("/")
async def root():
    return {"message": "Gakushu Nihongo API", "status": "ready"}


# ---------- Auth ----------
@api.post("/auth/register")
async def register(data: Credentials, response: Response):
    email = data.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "Email ini sudah terdaftar")
    user = {
        "id": str(uuid.uuid4()), "email": email,
        "name": data.name.strip() or email.split("@")[0],
        "password_hash": hash_password(data.password),
        "role": "learner", "must_change_password": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user)
    jti = set_session(response, user["id"])
    await db.sessions.insert_one({"jti": jti, "user_id": user["id"],
                                  "created_at": datetime.now(timezone.utc).isoformat()})
    return public_user(user)

@api.post("/auth/login")
async def login(data: Credentials, response: Response, request: Request):
    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (
        request.client.host if request.client else "unknown"
    )
    identifier = f"{client_ip}:{data.email.lower()}"
    now = datetime.now(timezone.utc)
    attempt = await db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    if attempt and attempt.get("locked_until") and datetime.fromisoformat(attempt["locked_until"]) > now:
        raise HTTPException(429, "Terlalu banyak percobaan. Coba lagi 15 menit lagi")
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user or not verify_password(data.password, user["password_hash"]):
        failures = (attempt.get("failures", 0) if attempt else 0) + 1
        update = {"failures": failures, "last_attempt": now.isoformat()}
        if failures >= 5:
            update["locked_until"] = (now + timedelta(minutes=15)).isoformat()
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$set": update, "$setOnInsert": {"identifier": identifier}}, upsert=True,
        )
        raise HTTPException(401, "Email atau password salah")
    await db.login_attempts.delete_one({"identifier": identifier})
    jti = set_session(response, user["id"])
    await db.sessions.insert_one({"jti": jti, "user_id": user["id"],
                                  "ip": client_ip,
                                  "created_at": datetime.now(timezone.utc).isoformat()})
    return public_user(user)

@api.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(current_user)):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Berhasil keluar"}

@api.get("/auth/me")
async def me(user: dict = Depends(current_user)):
    return public_user(user)

@api.post("/auth/refresh")
async def refresh(response: Response, refresh_token: Optional[str] = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(401, "Sesi tidak ditemukan")
    payload = decode_token(refresh_token, "refresh")
    session = await db.sessions.find_one({"jti": payload["jti"], "user_id": payload["sub"]}, {"_id": 0})
    if not session:
        raise HTTPException(401, "Sesi telah berakhir")
    await db.sessions.delete_one({"jti": payload["jti"]})
    new_jti = set_session(response, payload["sub"])
    await db.sessions.insert_one({"jti": new_jti, "user_id": payload["sub"],
                                  "created_at": datetime.now(timezone.utc).isoformat()})
    return {"message": "Sesi diperbarui"}

@api.post("/auth/forgot-password")
async def forgot_password(data: EmailRequest):
    email = data.email.lower()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(404, "Tidak ada akun untuk email ini")
    temporary = secrets.token_urlsafe(9)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": hash_password(temporary), "must_change_password": True,
                  "reset_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}},
    )
    return {
        "message": "Password sementara dibuat. Pakai sekali lalu ubah passwordnya.",
        "temporary_password": temporary,
    }

@api.post("/auth/change-password")
async def change_password(data: PasswordChange, user: dict = Depends(current_user)):
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(400, "Password saat ini salah")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": hash_password(data.new_password), "must_change_password": False},
         "$unset": {"reset_expires_at": ""}},
    )
    return {"message": "Password diperbarui"}


# ---------- Chapters (public / learner) ----------
def public_chapter(doc: dict, include_content: bool) -> dict:
    base = {
        "number": doc["number"],
        "book": doc["book"],
        "book_label": doc.get("book_label", f"Minna no Nihongo {doc['book']}"),
        "title": doc["title"],
        "title_translation": doc["title_translation"],
        "has_content": doc.get("has_content", True),
        "published": doc.get("published", True),
        "quiz_padded": doc.get("quiz_padded", False),
        "counts": {
            "bunpo": len((doc.get("content") or {}).get("bunpo", [])),
            "kotoba": len((doc.get("content") or {}).get("kotoba", [])),
            "kanji": len((doc.get("content") or {}).get("kanji", [])),
            "quiz_bunpo": len((doc.get("content") or {}).get("quiz_bunpo", [])),
            "quiz_susun": len((doc.get("content") or {}).get("quiz_susun", [])),
            "kaiwa_lines": len(((doc.get("content") or {}).get("kaiwa") or {}).get("dialog", [])),
        },
    }
    if include_content:
        base["content"] = doc.get("content", {})
    return base


@api.get("/chapters")
async def chapters_list():
    docs = await db.chapters.find({"published": True}, {"_id": 0}).sort("number", 1).to_list(200)
    return [public_chapter(d, include_content=False) for d in docs]


@api.get("/chapters/{number}")
async def chapter_detail(number: int):
    doc = await db.chapters.find_one({"number": number, "published": True}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Bab tidak ditemukan")
    # Strip quiz answer_index & correct info from public detail? Keep exposed so learner can see explanation after answering.
    # For fairness we strip answers only from what's shown BEFORE quiz submit — but frontend only requests correct after submit through /quiz endpoint.
    # Return with content but redact answers.
    content = dict(doc.get("content", {}))
    content["quiz_bunpo"] = [
        {k: v for k, v in q.items() if k not in {"answer_index", "explanation"}}
        for q in content.get("quiz_bunpo", [])
    ]
    content["quiz_susun"] = [
        {k: v for k, v in q.items() if k not in {"correct_order"}}
        # keep distractors to render buttons, but obscure correct order
        for q in content.get("quiz_susun", [])
    ]
    return {**public_chapter(doc, include_content=False), "content": content}


def _grade_bunpo(quiz_items: list[dict], answers: dict[str, Any]) -> dict:
    per_item = []
    correct = 0
    for q in quiz_items:
        picked = answers.get(q["id"])
        try:
            picked_i = int(picked) if picked is not None else -1
        except (TypeError, ValueError):
            picked_i = -1
        is_correct = picked_i == q.get("answer_index")
        if is_correct:
            correct += 1
        per_item.append({
            "id": q["id"], "picked": picked_i,
            "correct_index": q.get("answer_index"),
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })
    return {"correct": correct, "total": len(quiz_items), "items": per_item}


def _grade_susun(quiz_items: list[dict], answers: dict[str, Any]) -> dict:
    per_item = []
    correct = 0
    for q in quiz_items:
        picked_seq = answers.get(q["id"]) or []
        correct_seq = [seg["text"] for seg in q.get("correct_order", [])]
        picked_texts = [str(x) for x in picked_seq]
        is_correct = picked_texts == correct_seq
        if is_correct:
            correct += 1
        per_item.append({
            "id": q["id"], "picked": picked_texts,
            "correct_order": correct_seq,
            "is_correct": is_correct,
        })
    return {"correct": correct, "total": len(quiz_items), "items": per_item}


@api.post("/chapters/{number}/quiz")
async def submit_chapter_quiz(number: int, data: QuizSubmission, user: dict = Depends(learner)):
    doc = await db.chapters.find_one({"number": number, "published": True}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Bab tidak ditemukan")
    content = doc.get("content", {})
    if data.quiz_kind == "susun":
        graded = _grade_susun(content.get("quiz_susun", []), data.answers)
    else:
        graded = _grade_bunpo(content.get("quiz_bunpo", []), data.answers)
    total = max(graded["total"], 1)
    score = round(graded["correct"] / total * 100)
    attempt = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "chapter_number": number,
        "quiz_kind": data.quiz_kind,
        "operation_id": data.operation_id,
        "score": score,
        "correct": graded["correct"],
        "total": graded["total"],
        "items": graded["items"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.attempts.insert_one(attempt)
    except Exception:
        existing = await db.attempts.find_one(
            {"user_id": user["id"], "operation_id": data.operation_id}, {"_id": 0, "user_id": 0}
        )
        if existing:
            return existing
    if score >= 60:
        await db.progress.update_one(
            {"user_id": user["id"], "chapter_number": number, "section": f"quiz_{data.quiz_kind}"},
            {"$set": {"completed": True, "score": score,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    return public_attempt(attempt)


@api.get("/progress")
async def get_progress(user: dict = Depends(learner)):
    prog = await db.progress.find({"user_id": user["id"]}, {"_id": 0, "user_id": 0}).to_list(500)
    attempts = await db.attempts.find(
        {"user_id": user["id"]}, {"_id": 0, "user_id": 0, "items": 0}
    ).sort("created_at", -1).to_list(30)
    total_chapters = await db.chapters.count_documents({"published": True})
    done_numbers = {p["chapter_number"] for p in prog if p.get("completed")}
    return {
        "completed": len(done_numbers),
        "total_chapters": total_chapters,
        "progress": prog,
        "attempts": attempts,
    }


@api.put("/progress")
async def update_progress(data: ProgressUpdate, user: dict = Depends(learner)):
    now = datetime.now(timezone.utc).isoformat()
    await db.progress.update_one(
        {"user_id": user["id"], "chapter_number": data.chapter_number, "section": data.section},
        {"$set": {**data.model_dump(), "user_id": user["id"], "updated_at": now}},
        upsert=True,
    )
    return {"message": "Progres tersimpan", "chapter_number": data.chapter_number,
            "section": data.section, "updated_at": now}


# ---------- Admin ----------
@api.get("/admin/chapters")
async def admin_chapters(_: dict = Depends(admin_only)):
    docs = await db.chapters.find({}, {"_id": 0}).sort("number", 1).to_list(200)
    return [public_chapter(d, include_content=False) for d in docs]


@api.get("/admin/chapters/{number}")
async def admin_chapter_detail(number: int, _: dict = Depends(admin_only)):
    doc = await db.chapters.find_one({"number": number}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Bab tidak ditemukan")
    return public_chapter(doc, include_content=True)


@api.put("/admin/chapters/{number}")
async def admin_update_chapter(number: int, data: ChapterUpdate, _: dict = Depends(admin_only)):
    updates: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ("title", "title_translation", "published"):
        val = getattr(data, field)
        if val is not None:
            updates[field] = val
    if data.content is not None:
        # Allow partial content merge (bunpo/kotoba/etc.)
        existing = await db.chapters.find_one({"number": number}, {"_id": 0, "content": 1})
        if not existing:
            raise HTTPException(404, "Bab tidak ditemukan")
        merged = {**existing.get("content", {}), **data.content}
        updates["content"] = merged
    res = await db.chapters.update_one({"number": number}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(404, "Bab tidak ditemukan")
    doc = await db.chapters.find_one({"number": number}, {"_id": 0})
    return public_chapter(doc, include_content=True)


@api.post("/admin/chapters/{number}/publish")
async def admin_toggle_publish(number: int, _: dict = Depends(admin_only)):
    doc = await db.chapters.find_one({"number": number}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Bab tidak ditemukan")
    new_state = not doc.get("published", True)
    await db.chapters.update_one(
        {"number": number},
        {"$set": {"published": new_state, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"number": number, "published": new_state}


@api.post("/admin/chapters/{number}/pad-quiz")
async def admin_pad_quiz(number: int, _: dict = Depends(admin_only)):
    doc = await db.chapters.find_one({"number": number}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Bab tidak ditemukan")
    quiz = list((doc.get("content") or {}).get("quiz_bunpo", []))
    if len(quiz) >= 15:
        return {"number": number, "quiz_bunpo": len(quiz), "generated": 0,
                "quiz_padded": True, "message": "Quiz sudah punya ≥15 soal"}
    need = 15 - len(quiz)
    try:
        extras = await generate_extra_bunpo_questions(doc, need)
    except Exception as e:
        log.exception("LLM padding failed for chapter %s", number)
        raise HTTPException(502, f"Gagal generate soal: {e}") from e
    combined = quiz + extras
    content = dict(doc.get("content", {}))
    content["quiz_bunpo"] = combined
    await db.chapters.update_one(
        {"number": number},
        {"$set": {"content": content, "quiz_padded": len(combined) >= 15,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {
        "number": number, "quiz_bunpo": len(combined),
        "generated": len(extras), "quiz_padded": len(combined) >= 15,
        "message": f"Berhasil menambah {len(extras)} soal (total {len(combined)})",
    }


@api.post("/admin/chapters/{number}/reset")
async def admin_reset_chapter(number: int, _: dict = Depends(admin_only)):
    source = next((c for c in ALL_CHAPTERS if c["number"] == number), None)
    if not source:
        raise HTTPException(404, "Sumber bab tidak ditemukan")
    now = datetime.now(timezone.utc).isoformat()
    await db.chapters.update_one(
        {"number": number},
        {"$set": {
            "book": source["book"], "book_label": f"Minna no Nihongo {source['book']}",
            "title": source["title"], "title_translation": source["title_translation"],
            "has_content": source.get("has_content", True), "content": source["content"],
            "quiz_padded": False, "updated_at": now,
        }},
        upsert=True,
    )
    doc = await db.chapters.find_one({"number": number}, {"_id": 0})
    return public_chapter(doc, include_content=True)


app.include_router(api)
allowed_origins = [o for o in os.environ.get("FRONTEND_URL", "").split(",") if o]
if not allowed_origins:
    allowed_origins = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o and o != "*"]
app.add_middleware(
    CORSMiddleware, allow_credentials=True,
    allow_origins=allowed_origins or ["*"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
