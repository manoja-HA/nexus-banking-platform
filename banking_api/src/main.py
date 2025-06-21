import uvicorn
from fastapi import FastAPI
from internal.configs.app import AppConfig, load_app_config
from internal.helpers.app import build_fastapi_app

app: FastAPI = build_fastapi_app()

if __name__ == "__main__":
    config: AppConfig = load_app_config()
    uvicorn.run(  # type: ignore
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
    )
