from dotenv import load_dotenv
load_dotenv()

import os
from app.core.config import get_settings

# LangSmith tracing — must set env vars before LangChain is imported
_s = get_settings()
if _s.langchain_tracing_v2 and _s.langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = _s.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = _s.langsmith_project

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router

app = FastAPI(title="Smart Home Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
