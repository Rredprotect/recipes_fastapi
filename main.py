from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import recipe_router

app = FastAPI(
    title="Recipe API",
    description="API for managing recipes with ingredients",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipe_router)


@app.get("/", tags=["root"])
async def read_root() -> dict[str, str]:
    return {"message": "Recipe API is running"}
