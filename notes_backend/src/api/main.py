from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.notes import router as notes_router

openapi_tags = [
    {
        "name": "health",
        "description": "Service health endpoints.",
    },
    {
        "name": "notes",
        "description": "CRUD operations for notes.",
    },
]

app = FastAPI(
    title="Simple Notes API",
    description="FastAPI backend for a simple notes application (SQLite-backed).",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# Keep CORS enabled for the frontend (running on port 3000).
# If you want to tighten this further, set allow_origins=["http://localhost:3000", ...]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes_router)


@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Simple health endpoint to verify the API is running.",
    operation_id="health_check",
)
# PUBLIC_INTERFACE
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

