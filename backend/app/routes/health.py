from fastapi import APIRouter

HealthRouter = APIRouter()


@HealthRouter.get("/", tags=["Health"])
async def GetHealth():
    return {"Status": "ok"}
