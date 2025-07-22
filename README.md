# Whisper Lyrics Extractor Service

> FastAPI 기반의 음원 파일(whisper)로부터 자동으로 타임스탬프 가사를 추출하여 반환하는 서비스

---

## 🚀 프로젝트 개요

`Whisper Lyrics Extractor Service`는 주어진 음원 파일(URL or Firebase Storage)에 대해 `faster-whisper` 모델을 사용해 한국어 가사를 타임스탬프와 함께 추출합니다. 추출된 가사는 텍스트 파일로 저장되며, API 호출 시 JSON 형태로 반환됩니다.

---

## 🔧 주요 기능

* **음원 파일 로드**: 로컬 파일 또는 Firebase Storage에 저장된 MP3 파일
* **가사 추출**: `faster-whisper` 모델로 음성 인식(한국어) 및 세그먼트별 타임스탬프 생성
* **텍스트 저장**: `[start ~ end] 가사` 형식의 라인들을 `{basename}.txt`로 저장
* **REST API**: FastAPI로 JSON 응답 제공 (원본 텍스트 및 리스트)

---

## 📦 기술 스택

* **언어**: Python 3.9+
* **웹 프레임워크**: FastAPI
* **ASGI 서버**: Uvicorn
* **음성 인식**: faster-whisper (WhisperModel)
* **오디오 처리**: torchaudio, soundfile
* **클라우드 스토리지**: Firebase Storage via firebase-admin
* **추가 라이브러리**: requests, pydantic

---

## 📁 디렉터리 구조

```
Whisper-main/
├─ extract_lyrics.py          # Whisper 모델 사용 가사 추출 유틸리티
├─ lyrics.py                  # FastAPI 애플리케이션 엔트리포인트
├─ test.py                    # extract_lyrics 테스트 스크립트
├─ requirements.txt           # Python 패키지 의존성
└─ repository/
    └─ <firebase-adminsdk>.json  # Firebase 서비스 계정 키
```

---

## ⚙️ 설치 및 실행

1. **클론 및 디렉터리 이동**

   ```bash
   git clone <repo-url>
   cd Whisper-main
   ```

2. **의존성 설치**

   ```bash
   pip install -r requirements.txt
   ```

3. **Firebase 서비스 계정 설정**

   * `repository/` 폴더에 발급받은 `*.json` 키 파일 위치
   * `lyrics.py`에서 `firebase_admin.initialize_app()` 호출 시 해당 키 경로 지정

4. **API 서버 실행**

   ```bash
   uvicorn lyrics:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 🌐 API 사용 예시

### POST `/extract-lyrics`

**Request Body** (JSON)

```json
{
  "vocal_url": "https://storage.googleapis.com/<bucket>/vocals/filename_vocals.mp3"
}
```

**Response** (JSON)

```json
{
  "lyrics": "[0.00 ~ 10.00] 가사 예시...",
  "lines": [
    "[0.00 ~ 10.00] 첫 번째 가사",
    "[10.00 ~ 20.00] 두 번째 가사"
  ]
}
```

---

## 🛠 추가 정보

* **extract\_lyrics.py**: `WhisperModel` 로드 시 `device` 자동 감지 (CUDA/CPU)
* **parameters**: `beam_size`, `temperature`, `vad_filter` 등을 조정 가능
* **결과 파일**: `{basename}.txt`로 로컬 저장

---

## 🚀 향후 개선 포인트

* **멀티파일 지원**: 여러 오디오 파일 일괄 처리
* **클라우드 배포**: Dockerize + AWS/GCP 배포 자동화
* **RAG 연동**: 추출된 가사 기반 질의응답 기능 추가
* **STT 옵션**: 한국어 외 다국어 지원

---