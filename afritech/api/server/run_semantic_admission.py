import uvicorn

from afritech.api.semantic_admission import app


if __name__ == "__main__":
    uvicorn.run(
        "afritech.api.server.run_semantic_admission:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
