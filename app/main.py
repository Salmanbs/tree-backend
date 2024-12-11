from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models

from app.database import engine, SessionLocal
from utils.seeder import seed_data

from app.tree.routes import tree_router
from app.tags.routes import tags_router

app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

models.Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    # Seed the database
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


# Include router
app.include_router(tree_router)
app.include_router(tags_router)
