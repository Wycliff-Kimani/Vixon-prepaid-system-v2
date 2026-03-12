from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import Base, engine
from routers import auth as auth_router
from routers import admin as admin_router
from routers import packages as packages_router
from routers import balance as balance_router
from routers import machine as machine_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vixon Prepaid System V2",
    version="2.0.0",
    swagger_ui_parameters={"persistAuthorization": True}
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
app.include_router(machine_router.router)

from fastapi import Request
from fastapi.responses import HTMLResponse

@app.get("/machine-screen", response_class=HTMLResponse)
def machine_screen(request: Request):
    return templates.TemplateResponse("machine.html", {"request": request})

@app.get("/")
def root():
    return {"message": "Vixon V2 API is running", "docs": "/docs"}