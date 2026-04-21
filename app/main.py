from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.octoclick import router as octoclick_router
from app.api.routes.review import router as review_router
from app.api.routes.exports import router as exports_router

app = FastAPI(title="Scriptor v1")
app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(octoclick_router)
app.include_router(review_router)
app.include_router(exports_router)
