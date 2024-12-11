from pydantic import BaseModel
from typing import List, Annotated, Optional


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
    id: Optional[int] = None


TagRequest.update_forward_refs()  # Enable recursive definition


class SaveTreeRequest(BaseModel):
    tree: List[dict]
    name: str
    id: Optional[int] = None
