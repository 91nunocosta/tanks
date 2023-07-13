from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from .dependencies import get_settings
from .routers.tank_volumes import router as tank_volumes_router
from .routers.tanksr import router as tanks_router


def handle_not_found(_request, _exc):
    return JSONResponse(content={"message": "Item not found."}, status_code=404)


def create_app():
    get_settings()
    app = FastAPI()
    app.include_router(tanks_router)
    app.include_router(tank_volumes_router)
    app.add_exception_handler(NoResultFound, handle_not_found)
    return app
