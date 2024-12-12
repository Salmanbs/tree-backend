from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import db_dependency
from app import models

from app.schemas import (
    SaveTreeRequest,
)

tree_router = APIRouter()


def build_tag_tree(tag: models.Tag, db: Session):
    children = (
        db.query(models.Tag)
        .filter(models.Tag.parent_id == tag.id)
        .order_by(models.Tag.order)
        .all()
    )
    return {
        "id": tag.id,
        "name": tag.name,
        "data": tag.data,
        "children": [build_tag_tree(child, db) for child in children],
    }


@tree_router.get("/trees")
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


@tree_router.post("/trees/save")
async def save_tree(request: SaveTreeRequest, db: db_dependency):
    def save_tags(tree, parent_id=None, tree_id=None):
        for tag in tree:
            # Check if the tag exists, create or update as needed
            if "id" in tag:
                tag_obj = (
                    db.query(models.Tag).filter(models.Tag.id == tag["id"]).first()
                )
                if tag_obj:
                    tag_obj.name = tag["name"]
                    tag_obj.data = tag.get("data")
                    tag_obj.parent_id = parent_id
                    db.commit()
                    db.refresh(tag_obj)
                else:
                    raise HTTPException(
                        status_code=404, detail=f"Tag with id {tag['id']} not found."
                    )
            else:
                # Create a new tag if no ID is provided
                tag_obj = models.Tag(
                    name=tag["name"],
                    data=tag.get("data"),
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
        if request.id:
            # Modify an existing tree
            tree_obj = (
                db.query(models.Tree).filter(models.Tree.id == request.id).first()
            )
            if not tree_obj:
                raise HTTPException(
                    status_code=404, detail=f"Tree with id {request.id} not found."
                )

            # Update tree name
            tree_obj.name = request.name
            db.commit()
            db.refresh(tree_obj)

            # Update tags
            for tree in request.tree:
                if "id" in tree:
                    tag_obj = (
                        db.query(models.Tag).filter(models.Tag.id == tree["id"]).first()
                    )
                    if tag_obj:
                        tag_obj.name = tree["name"]
                        tag_obj.data = tree.get("data")
                        db.commit()
                        db.refresh(tag_obj)
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Tag with id {tree['id']} not found.",
                        )
                else:
                    # Save new root tags for existing tree
                    save_tags([tree], parent_id=None, tree_id=tree_obj.id)

        else:
            # Create a new tree
            tree_obj = models.Tree(name=request.name)
            db.add(tree_obj)
            db.commit()
            db.refresh(tree_obj)

            # Save new tree hierarchy
            for tree in request.tree:
                save_tags([tree], parent_id=None, tree_id=tree_obj.id)

        return {"status": "success", "message": "Tree hierarchy processed successfully"}
    except Exception as e:
        # Rollback the transaction in case of error
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
