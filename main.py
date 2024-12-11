from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Annotated, Optional
import models

from database import engine, SessionLocal, Base
from sqlalchemy.orm import Session
from seeder import seed_data


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


class TagBase(BaseModel):
    name: str
    data: str


class AddChildRequest(BaseModel):
    parent_id: int


class UpdateTagRequest(BaseModel):
    name: str
    data: str


class TagRequest(BaseModel):
    name: str
    data: Optional[str] = None
    children: Optional[List["TagRequest"]] = []


TagRequest.update_forward_refs()  # Enable recursive definition


class SaveTreeRequest(BaseModel):
    tree: List[dict]
    name: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    # Seed the database
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# Recursive function to build the tag tree
def build_tag_tree(tag: models.Tag, db: Session):
    children = db.query(models.Tag).filter(models.Tag.parent_id == tag.id).all()
    return {
        "id": tag.id,
        "name": tag.name,
        "data": tag.data,
        "children": [build_tag_tree(child, db) for child in children],
    }


@app.get("/trees")
async def get_trees(db: db_dependency):
    trees = db.query(models.Tree).all()
    result = []
    for tree in trees:
        root_tags = (
            db.query(models.Tag)
            .filter(models.Tag.tree_id == tree.id, models.Tag.parent_id == None)
            .all()
        )
        result.append(
            {
                "id": tree.id,
                "name": tree.name,
                "tree": [build_tag_tree(tag, db) for tag in root_tags],
            }
        )
    return result


@app.post("/tags/add-child")
async def add_child(request: AddChildRequest, db: db_dependency):
    # Fetch the parent tag
    parent_tag = db.query(models.Tag).filter(models.Tag.id == request.parent_id).first()

    if not parent_tag:
        raise HTTPException(status_code=404, detail="Parent tag not found")

    # Clear `data` if the parent tag has it
    if parent_tag.data:
        parent_tag.data = None

    # Create a new child tag
    new_child = models.Tag(
        name="New Child",
        data="Data",
        parent_id=parent_tag.id,
        tree_id=parent_tag.tree_id,  # Associate with the same tree
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)

    # Return the updated tag tree structure
    updated_tree = (
        db.query(models.Tag)
        .filter(models.Tag.tree_id == parent_tag.tree_id, models.Tag.parent_id == None)
        .all()
    )
    return {"tree": [build_tag_tree(tag, db) for tag in updated_tree]}


@app.put("/tags/{tag_id}")
async def update_tag(tag_id: int, request: UpdateTagRequest, db: db_dependency):
    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Update the tag properties
    tag.name = request.name
    tag.data = request.data
    db.commit()
    db.refresh(tag)

    return {"id": tag.id, "name": tag.name, "data": tag.data}


@app.post("/trees/save")
async def save_tree(request: SaveTreeRequest, db: db_dependency):
    def save_tags(tree, parent_id=None, tree_id=None):
        for tag in tree:
            # Create a new Tag object
            tag_obj = models.Tag(
                name=tag["name"],
                data=tag.get("data"),  # Handle optional data field
                parent_id=parent_id,
                tree_id=tree_id,
            )
            db.add(tag_obj)
            db.commit()
            db.refresh(tag_obj)

            # Recursively save children
            if "children" in tag and tag["children"]:
                save_tags(tag["children"], parent_id=tag_obj.id, tree_id=tree_id)

    try:
        # Delete existing tags and trees (if needed)
        db.query(models.Tag).delete()
        db.query(models.Tree).delete()
        db.commit()

        # Create a new Tree object
        tree_obj = models.Tree(name=request.name)
        db.add(tree_obj)
        db.commit()
        db.refresh(tree_obj)

        # Save new tree hierarchy
        for tree in request.tree:
            # Save associated tags recursively

            tag_obj = models.Tag(
                name=tree["name"],
                data=tree.get("data"),  # Handle optional data field
                parent_id=None,
                tree_id=tree_obj.id,
            )
            db.add(tag_obj)
            db.commit()
            db.refresh(tag_obj)

            if "children" in tree:
                save_tags(tree["children"], parent_id=tag_obj.id, tree_id=tree_obj.id)

        return {"status": "success", "message": "Tree hierarchy saved successfully"}
    except Exception as e:
        # Rollback the transaction in case of error
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/tags")
async def get_tags():
    return "hi"


@app.post("/tags")
async def create_tag(tag: TagBase, db: db_dependency):
    db_tag = models.Tag(name=tag.name, data=tag.data)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag
