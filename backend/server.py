from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import hashlib
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

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
JWT_ALGORITHM = "HS256"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

app = FastAPI(title="Gakushu Nihongo API")
api = APIRouter(prefix="/api")
logging.basicConfig(level=logging.INFO)

class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=80)

class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8, max_length=128)

class QuizSubmission(BaseModel):
    answers: dict[str, int]
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ProgressUpdate(BaseModel):
    lesson_id: str
    resume_position: int = Field(default=0, ge=0)
    completed: bool = False

class EmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def token_secret() -> str:
    return os.environ["JWT_SECRET"]

def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {"id": str(user["id"]), "email": user["email"], "name": user.get("name", ""), "role": user.get("role", "learner"), "must_change_password": user.get("must_change_password", False)}

def make_token(user_id: str, token_type: str, expiry: timedelta, jti: Optional[str] = None) -> str:
    return jwt.encode({"sub": user_id, "type": token_type, "jti": jti or str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + expiry}, token_secret(), algorithm=JWT_ALGORITHM)

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
    response.set_cookie("access_token", access, httponly=True, secure=COOKIE_SECURE, samesite="lax", max_age=900, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=COOKIE_SECURE, samesite="lax", max_age=604800, path="/")
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

async def seed_content():
    if await db.lessons.count_documents({}) == 0:
        await db.lessons.insert_many([
            {"id": "lesson-01", "number": "01", "title": "はじめまして", "subtitle": "Nice to meet you", "level": "Starter", "duration": 18, "description": "Introduce yourself, ask names, and use the first phrases that open every Japanese conversation.", "published": True, "accent": "vermilion", "vocabulary": [{"word": "わたし", "reading": "watashi", "meaning": "I / me"}, {"word": "せんせい", "reading": "sensei", "meaning": "teacher"}, {"word": "がくせい", "reading": "gakusei", "meaning": "student"}], "quiz": [{"id": "q1", "prompt": "What does わたし mean?", "options": ["Teacher", "I / me", "Student", "Friend"], "answer": 1}, {"id": "q2", "prompt": "せんせい is a…", "options": ["student", "friend", "teacher", "name"], "answer": 2}]},
            {"id": "lesson-02", "number": "02", "title": "これ・それ・あれ", "subtitle": "Things around us", "level": "Starter", "duration": 22, "description": "Point to objects and describe what belongs to you or someone else.", "published": True, "accent": "indigo", "vocabulary": [{"word": "これ", "reading": "kore", "meaning": "this"}, {"word": "それ", "reading": "sore", "meaning": "that"}, {"word": "ほん", "reading": "hon", "meaning": "book"}], "quiz": [{"id": "q1", "prompt": "これ means…", "options": ["this", "that over there", "where", "book"], "answer": 0}]},
            {"id": "lesson-03", "number": "03", "title": "ここ・そこ・あそこ", "subtitle": "Places and directions", "level": "Starter", "duration": 20, "description": "Ask where things are and navigate familiar places with confidence.", "published": True, "accent": "teal", "vocabulary": [{"word": "ここ", "reading": "koko", "meaning": "here"}, {"word": "そこ", "reading": "soko", "meaning": "there"}, {"word": "えき", "reading": "eki", "meaning": "station"}], "quiz": [{"id": "q1", "prompt": "えき means…", "options": ["school", "station", "shop", "home"], "answer": 1}]},
        ])

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.sessions.create_index("jti", unique=True)
    await db.progress.create_index([("user_id", 1), ("lesson_id", 1)], unique=True)
    await db.attempts.create_index([("user_id", 1), ("operation_id", 1)], unique=True)
    await db.users.create_index("reset_expires_at", expireAfterSeconds=0)
    await seed_content()
    admin_email, admin_password = os.environ.get("ADMIN_EMAIL"), os.environ.get("ADMIN_PASSWORD")
    if admin_email and admin_password and not await db.users.find_one({"email": admin_email.lower()}):
        await db.users.insert_one({"id": str(uuid.uuid4()), "email": admin_email.lower(), "name": "Content editor", "password_hash": hash_password(admin_password), "role": "admin", "must_change_password": False, "created_at": datetime.now(timezone.utc).isoformat()})

@api.get("/")
async def root():
    return {"message": "Gakushu Nihongo API", "status": "ready"}

@api.post("/auth/register")
async def register(data: Credentials, response: Response):
    email = data.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "An account with this email already exists")
    user = {"id": str(uuid.uuid4()), "email": email, "name": data.name.strip() or email.split("@")[0], "password_hash": hash_password(data.password), "role": "learner", "must_change_password": False, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one(user)
    jti = set_session(response, user["id"])
    await db.sessions.insert_one({"jti": jti, "user_id": user["id"], "created_at": datetime.now(timezone.utc).isoformat()})
    return public_user(user)

@api.post("/auth/login")
async def login(data: Credentials, response: Response, request: Request):
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect")
    jti = set_session(response, user["id"])
    await db.sessions.insert_one({"jti": jti, "user_id": user["id"], "ip": request.client.host if request.client else None, "created_at": datetime.now(timezone.utc).isoformat()})
    return public_user(user)

@api.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(current_user)):
    response.delete_cookie("access_token", path="/"); response.delete_cookie("refresh_token", path="/")
    return {"message": "Signed out"}

@api.get("/auth/me")
async def me(user: dict = Depends(current_user)):
    return public_user(user)

@api.post("/auth/refresh")
async def refresh(response: Response, refresh_token: Optional[str] = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(401, "No refresh session")
    payload = decode_token(refresh_token, "refresh")
    session = await db.sessions.find_one({"jti": payload["jti"], "user_id": payload["sub"]}, {"_id": 0})
    if not session:
        raise HTTPException(401, "Refresh session expired")
    await db.sessions.delete_one({"jti": payload["jti"]})
    new_jti = set_session(response, payload["sub"])
    await db.sessions.insert_one({"jti": new_jti, "user_id": payload["sub"], "created_at": datetime.now(timezone.utc).isoformat()})
    return {"message": "Session refreshed"}

@api.post("/auth/forgot-password")
async def forgot_password(data: EmailRequest):
    email = data.email.lower()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(404, "No account found for this email")
    temporary = secrets.token_urlsafe(9)
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_password(temporary), "must_change_password": True, "reset_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}})
    return {"message": "A temporary password was generated. Use it once, then choose a new password.", "temporary_password": temporary}

@api.post("/auth/change-password")
async def change_password(data: PasswordChange, user: dict = Depends(current_user)):
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(400, "Current password is incorrect")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_password(data.new_password), "must_change_password": False}, "$unset": {"reset_expires_at": ""}})
    return {"message": "Password updated"}

@api.get("/lessons")
async def lessons():
    docs = await db.lessons.find({"published": True}, {"_id": 0, "quiz": 0, "vocabulary": 0}).sort("number", 1).to_list(100)
    return docs

@api.get("/lessons/{lesson_id}")
async def lesson_detail(lesson_id: str):
    doc = await db.lessons.find_one({"id": lesson_id, "published": True}, {"_id": 0})
    if not doc: raise HTTPException(404, "Lesson not found")
    return doc

@api.get("/progress")
async def get_progress(user: dict = Depends(learner)):
    docs = await db.progress.find({"user_id": user["id"]}, {"_id": 0, "user_id": 0}).to_list(100)
    attempts = await db.attempts.find({"user_id": user["id"]}, {"_id": 0, "user_id": 0, "answers": 0}).sort("created_at", -1).to_list(20)
    return {"completed": sum(1 for item in docs if item.get("completed")), "total_lessons": await db.lessons.count_documents({"published": True}), "progress": docs, "attempts": attempts}

@api.put("/progress")
async def update_progress(data: ProgressUpdate, user: dict = Depends(learner)):
    now = datetime.now(timezone.utc).isoformat()
    await db.progress.update_one({"user_id": user["id"], "lesson_id": data.lesson_id}, {"$set": {**data.model_dump(), "user_id": user["id"], "updated_at": now}}, upsert=True)
    return {"message": "Progress saved", "lesson_id": data.lesson_id, "updated_at": now}

@api.post("/lessons/{lesson_id}/quiz")
async def submit_quiz(lesson_id: str, data: QuizSubmission, user: dict = Depends(learner)):
    lesson = await db.lessons.find_one({"id": lesson_id, "published": True}, {"_id": 0})
    if not lesson: raise HTTPException(404, "Lesson not found")
    correct = sum(1 for question in lesson["quiz"] if data.answers.get(question["id"]) == question["answer"])
    attempt = {"id": str(uuid.uuid4()), "user_id": user["id"], "lesson_id": lesson_id, "operation_id": data.operation_id, "score": round(correct / len(lesson["quiz"]) * 100), "created_at": datetime.now(timezone.utc).isoformat()}
    try: await db.attempts.insert_one(attempt)
    except Exception:
        existing = await db.attempts.find_one({"user_id": user["id"], "operation_id": data.operation_id}, {"_id": 0, "user_id": 0, "answers": 0})
        if existing:
            return existing
        return {k: v for k, v in attempt.items() if k != "user_id"}
    return {k: v for k, v in attempt.items() if k != "user_id"}

app.include_router(api)
allowed_origins = [o for o in os.environ.get("FRONTEND_URL", "").split(",") if o]
if not allowed_origins:
    allowed_origins = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o and o != "*"]
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=allowed_origins, allow_methods=["*"], allow_headers=["*"])

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()