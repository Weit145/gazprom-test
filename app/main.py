import logging
from .core.logging import setup_logging

from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI, status


logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения")
    yield
    logger.info("Остановка приложения")


app = FastAPI(
    lifespan=lifespan,
    title="Gazprom TEST",
    swagger_ui_parameters={"persistAuthorization": True},
)

@app.get("/_info", status_code=status.HTTP_200_OK)
async def info():
    return status.HTTP_200_OK


if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)
