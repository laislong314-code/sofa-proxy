"""
sofa_proxy — API proxy para o SofaScore
Roda no Railway (IP não bloqueado pelo Cloudflare)
A EC2 consome esta API em vez de chamar o SofaScore diretamente.

Endpoints:
  GET /scheduled/{date}          → jogos do dia (YYYY-MM-DD)
  GET /event/{event_id}/stats    → estatísticas + xG do jogo
  GET /health                    → healthcheck
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from curl_cffi import requests as cfrequests
import os

app = FastAPI(title="SofaScore Proxy", version="1.0.0")

BASE = "https://api.sofascore.com/api/v1"
SESSION = cfrequests.Session()

# Token opcional para proteger a API (defina PROXY_TOKEN no Railway)
PROXY_TOKEN = os.getenv("PROXY_TOKEN", "")


def _check_token(request):
    if not PROXY_TOKEN:
        return  # sem token configurado, API aberta
    token = request.headers.get("X-Proxy-Token", "")
    if token != PROXY_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def sofa_get(path: str) -> dict:
    url = f"{BASE}{path}"
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


@app.get("/scheduled/{date}")
def scheduled_events(date: str, request: None = None):
    """
    Retorna todos os jogos de futebol de uma data.
    date: YYYY-MM-DD
    """
    data = sofa_get(f"/sport/football/scheduled-events/{date}")
    return JSONResponse(content=data)


@app.get("/event/{event_id}/stats")
def event_stats(event_id: int):
    """
    Retorna estatísticas (incluindo xG) de um jogo específico.
    """
    data = sofa_get(f"/event/{event_id}/statistics")
    return JSONResponse(content=data)


@app.get("/event/{event_id}/lineups")
def event_lineups(event_id: int):
    """
    Retorna lineups e stats individuais dos jogadores.
    """
    data = sofa_get(f"/event/{event_id}/lineups")
    return JSONResponse(content=data)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
