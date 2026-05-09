import uvicorn
from api.server.api_server import create_app

BASE_PATH = "."

app = create_app(BASE_PATH)

if __name__ == "__main__":
    uvicorn.run(
        "api.server.run_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )