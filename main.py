import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from config import IN_FILE, OUT_FILE
from logger import log
from pipeline import ask_tool, run


async def keep_warm():
    while True:
        try:
            await ask_tool("search_knowledge", "warm up")
        except Exception as e:
            log.warning(f"MCP abhi nahi mila ({e}) - agle minute phir try karenge")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(keep_warm())
    yield
    task.cancel()


app = FastAPI(title="Real Estate Voice Assistant", lifespan=lifespan)
PAGE = Path(__file__).with_name("templates") / "index.html"


@app.get("/")
def home():
    return FileResponse(PAGE)


@app.post("/chat")
async def chat(file: UploadFile):
    audio = await file.read()
    log.info(f"audio size = {len(audio)} bytes")

    with open(IN_FILE, "wb") as f:
        f.write(audio)

    try:
        user, ai, meta = await run(IN_FILE, OUT_FILE)
        return {"user": user, "ai": ai, "meta": meta}
    except Exception as e:
        log.error(f"FAIL | {e}")
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/audio")
def audio():
    return FileResponse(OUT_FILE, media_type="audio/mpeg")
