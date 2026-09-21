from __future__ import annotations

import os
import threading
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from starlette.concurrency import run_in_threadpool

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.txt"

HOST = "0.0.0.0"
PORT = 8000

MAX_BODY_BYTES = 64 * 1024
MAX_MESSAGE_LEN = 10_000

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

_file_lock = threading.Lock()


class MessagePayload(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Сообщение не может быть пустым")
        if len(value) > MAX_MESSAGE_LEN:
            raise ValueError(f"Сообщение длиннее {MAX_MESSAGE_LEN} символов")
        return value.replace("\r\n", "\n").replace("\r", "\n")


app = FastAPI(title="Отправка данных")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    raw_length = request.headers.get("content-length")
    if raw_length is not None:
        try:
            length = int(raw_length)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Некорректный Content-Length"},
            )
        if length > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Слишком большой объём данных"},
            )
    return await call_next(request)


def _append_to_file(text: str) -> None:
    with _file_lock:
        with open(DATA_FILE, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
            fh.flush()
            os.fsync(fh.fileno())


def _read_file() -> str:
    with _file_lock:
        if not DATA_FILE.exists():
            return ""
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            return fh.read()



@app.post("/api/data")
async def save_data(payload: MessagePayload):
    try:
        await run_in_threadpool(_append_to_file, payload.message)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сохранить данные: {exc.strerror or exc}",
        )
    return {"status": "ok", "message": "Данные сохранены"}


@app.get("/api/data")
async def get_data():
    try:
        content = await run_in_threadpool(_read_file)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось прочитать данные: {exc.strerror or exc}",
        )

    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Записи в файле отсутствуют",
        )

    return {"status": "ok", "content": content}


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")