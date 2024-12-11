from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from app.database import Base
from sqlalchemy.orm import relationship


class Tree(Base):
    __tablename__ = "trees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    data = Column(String, nullable=True)  # Nullable if the tag has children
    parent_id = Column(Integer, ForeignKey("tags.id"), nullable=True)
    tree_id = Column(Integer, ForeignKey("trees.id"), nullable=False)
    order = Column(Integer, nullable=True)

    # Relationships
    parent = relationship("Tag", remote_side=[id], backref="children")
