from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import db_dependency
from app import models

from app.schemas import (
    AddChildRequest,
    UpdateTagRequest,
    SaveTreeRequest,
)

tags_router = APIRouter()


@tags_router.post("/tags/add-child")
async def add_child(request: AddChildRequest, db: db_dependency):
    # Fetch the parent tag
    parent_tag = db.query(models.Tag).filter(models.Tag.id == request.parent_id).first()

    if not parent_tag:
        raise HTTPException(status_code=404, detail="Parent tag not found")

    # Clear `data` if the parent tag has it
    if parent_tag.data:
        parent_tag.data = None

    # Determine the order for the new child
    max_order = (
        db.query(models.Tag)
        .filter(models.Tag.parent_id == parent_tag.id)
        .order_by(models.Tag.order.desc())
        .first()
    )
    new_order = (max_order.order + 1) if max_order else 0

    # Create a new child tag
    new_child = models.Tag(
        name="New Child",
        data="Data",
        parent_id=parent_tag.id,
        tree_id=parent_tag.tree_id,  # Associate with the same tree
        order=new_order,
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)

    return new_child


@tags_router.put("/tags/{tag_id}")
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
