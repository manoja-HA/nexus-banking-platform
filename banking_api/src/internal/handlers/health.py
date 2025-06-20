from fastapi.routing import APIRouter

router: APIRouter = APIRouter()


@router.get("/health", summary="Health check.")
def get() -> str:
    """Health check"""
    return "success"
