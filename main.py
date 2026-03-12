from fastapi import FastAPI
from database import Base, engine
from routers import auth as auth_router
from routers import admin as admin_router
from routers import packages as packages_router
from routers import balance as balance_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vixon Prepaid System V2",
    version="2.0.0",
    swagger_ui_parameters={"persistAuthorization": True}
)

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="Vixon Prepaid System V2",
        version="2.0.0",
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi_schema = None
app.openapi = custom_openapi

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(packages_router.router)
app.include_router(balance_router.router)

@app.get("/")
def root():
    return {"message": "Vixon V2 API is running", "docs": "/docs"}