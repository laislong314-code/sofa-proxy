"""
sofa_proxy — API proxy genérico para o SofaScore
Roda no Railway (IP não bloqueado pelo Cloudflare)
A EC2 consome esta API em vez de chamar o SofaScore diretamente.

Qualquer path é repassado diretamente ao SofaScore:
  GET /sport/football/scheduled-events/2026-03-04
  GET /event/12345/statistics
  GET /event/12345/lineups
  etc.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
from curl_cffi import requests as cfrequests
import os

app = FastAPI(title="SofaScore Proxy", version="1.0.0")

BASE = "https://api.sofascore.com/api/v1"
SESSION = cfrequests.Session()

PROXY_TOKEN = os.getenv("PROXY_TOKEN", "")


def _check_token(request: Request):
    if not PROXY_TOKEN:
        return
    token = request.headers.get("X-Proxy-Token", "")
    if token != PROXY_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def sofa_get(path: str) -> dict:
    url = f"{BASE}/{path}"
    r = SESSION.get(url, impersonate="chrome124", timeout=20)
    if r.status_code != 200:
        raise HTTPException(
            status_code=r.status_code,
            detail=f"SofaScore returned {r.status_code}: {r.text[:200]}"
        )
    return r.json()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/{path:path}")
def proxy(path: str, request: Request):
    """Proxy genérico — repassa qualquer path direto ao SofaScore."""
    _check_token(request)
    data = sofa_get(path)
    return JSONResponse(content=data)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
