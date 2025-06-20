from fastapi import FastAPI
from internal.handlers import account, customer, health, transfer


def build_fastapi_app() -> FastAPI:
    fastapi_app: FastAPI = FastAPI(
        title="Banking API",
        version="0.1.0",
        description="API for Banking",
    )

    # Add routes
    fastapi_app.include_router(health.router, tags=["Health"])
    fastapi_app.include_router(account.router, tags=["Account"])
    fastapi_app.include_router(transfer.router, tags=["Transfer"])
    fastapi_app.include_router(customer.router, tags=["Customer"])

    return fastapi_app
