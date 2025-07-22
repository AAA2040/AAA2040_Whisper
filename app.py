from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import tempfile
import os
import torch
import firebase_admin
from firebase_admin import credentials
import traceback
from extract_lyrics import extract_lyrics
from firebase_admin import storage
import re
import json
import shutil

# ✅ FastAPI 앱 초기화
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Firebase Admin SDK 키 파일 경로
FIREBASE_KEY_PATH = "repository/key.json"


# Firebase 초기화 함수
def initialize_firebase():
    try:
        if firebase_admin._apps:
            # 이미 초기화된 경우 앱 삭제
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)

        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(
            cred, {"storageBucket": "aaa2040-c4b67.firebasestorage.app"}
        )
    except Exception as e:
        print(f"Firebase 초기화 실패: {str(e)}")
        raise e


# 초기 Firebase 초기화
try:
    initialize_firebase()
except Exception as e:
    print(f"초기 Firebase 초기화 실패: {str(e)}")


# ✅ 요청 바디 모델 정의
class DirectLyricsRequest(BaseModel):
    vocal_url: str


@app.get("/", response_class=HTMLResponse)
async def developer_page(request: Request):
    firebase_key_content = None
    try:
        if os.path.exists(FIREBASE_KEY_PATH):
            with open(FIREBASE_KEY_PATH, "r", encoding="utf-8") as f:
                firebase_key_content = json.dumps(json.load(f), indent=2)
    except Exception as e:
        print(f"Firebase 키 파일 읽기 실패: {str(e)}")

    return templates.TemplateResponse(
        "developer.html",
        {"request": request, "firebase_key_content": firebase_key_content},
    )


@app.post("/upload_firebase_key")
async def upload_firebase_key(request: Request, firebase_key: UploadFile = File(...)):
    try:
        # 파일 확장자 검사
        if not firebase_key.filename.endswith(".json"):
            return templates.TemplateResponse(
                "developer.html",
                {
                    "request": request,
                    "upload_message": "JSON 파일만 업로드 가능합니다.",
                    "upload_error": True,
                },
            )

        # repository 디렉토리가 없으면 생성
        os.makedirs("repository", exist_ok=True)

        # 파일 저장
        with open(FIREBASE_KEY_PATH, "wb") as buffer:
            shutil.copyfileobj(firebase_key.file, buffer)

        # Firebase 재초기화
        initialize_firebase()

        # 성공 응답
        return templates.TemplateResponse(
            "developer.html",
            {
                "request": request,
                "upload_message": "Firebase Admin SDK 키가 성공적으로 업로드되었습니다.",
                "upload_error": False,
                "firebase_key_content": open(
                    FIREBASE_KEY_PATH, "r", encoding="utf-8"
                ).read(),
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "developer.html",
            {
                "request": request,
                "upload_message": f"업로드 실패: {str(e)}",
                "upload_error": True,
            },
        )


@app.post("/lyrics")
async def extract_lyrics_direct(request: Request):
    print("[디버그] 요청 수신: /lyrics")
    try:
        data = await request.json()
        print(f"[디버그] 요청 바디: {data}")
        vocal_url = data.get("vocal_url")
        if not vocal_url:
            print("[에러] vocal_url이 없습니다.")
            raise HTTPException(status_code=400, detail="vocal_url이 필요합니다.")

        # "vocals/" 뒤의 문자열만 추출
        match = re.search(r"vocals/([^/?]+)", vocal_url)
        if match:
            filename = match.group(1)  # QW_TSknSbWM_vocals.mp3
            bucket_path = f"vocals/{filename}"
        else:
            print("[에러] vocal_url에서 vocals/ 경로를 찾을 수 없습니다.")
            raise HTTPException(
                status_code=400, detail="vocal_url 형식이 잘못되었습니다."
            )

        # 1. Firebase Storage에서 mp3 다운로드
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name
        bucket = storage.bucket()
        blob = bucket.blob(bucket_path)
        blob.download_to_filename(tmp_path)
        print(f"[디버그] Firebase에서 {bucket_path} → {tmp_path} 다운로드 완료")

        # 2. extract_lyrics로 가사 추출
        print(f"[디버그] extract_lyrics 함수 호출 시작: {tmp_path}")
        lines = extract_lyrics(tmp_path)
        text = "\n".join(lines)
        print(f"[디버그] extract_lyrics 결과 일부: {text[:100]}...")

        # 임시 파일 삭제
        os.remove(tmp_path)
        print(f"[디버그] 임시 파일 삭제 완료: {tmp_path}")

        # 결과 반환 (lines도 함께 반환)
        print("[디버그] 가사 추출 완료, 결과 반환")
        return {"lyrics": text, "lines": lines}

    except Exception as e:
        print(f"[에러] {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
