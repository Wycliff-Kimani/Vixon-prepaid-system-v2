from fastapi import FastAPI
from database import Base, engine
from routers import auth as auth_router
from routers import admin as admin_router
from routers import packages as packages_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vixon Prepaid System V2", version="2.0.0")

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(packages_router.router)

@app.get("/")
def root():
    return {"message": "Vixon V2 API is running", "docs": "/docs"}