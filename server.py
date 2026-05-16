from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from modules.constants import EVENT_NAME, ROOT_PATH, SQLITE_FILE
from modules.sqlite_helpers import maybe_create_tables


@asynccontextmanager
async def lifespan(_: FastAPI):
    maybe_create_tables(SQLITE_FILE)
    yield


app = FastAPI(root_path=ROOT_PATH, lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"status": "ok", "event": EVENT_NAME}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9191, reload=True)
