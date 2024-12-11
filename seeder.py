from sqlalchemy.orm import Session
from models import Tree, Tag


def seed_data(db: Session):
    # Check if data already exists to avoid duplicate seeding
    if db.query(Tree).first():
        print("Data already seeded. Skipping seeding.")
        return

    # Create initial tree
    tree = Tree(name="Example Tree")
    db.add(tree)
    db.commit()
    db.refresh(tree)

    # Add tags to the tree
    root = Tag(name="root", tree_id=tree.id, order=0)
    db.add(root)
    db.commit()
    db.refresh(root)

    # Add child tags with explicit order
    child1 = Tag(name="child1", parent_id=root.id, tree_id=tree.id, order=0)
    db.add(child1)
    db.commit()
    db.refresh(child1)

    child2 = Tag(
        name="child2", data="c2 World", parent_id=root.id, tree_id=tree.id, order=1
    )
    db.add(child2)

    # Add grandchildren tags with explicit order
    db.add_all(
        [
            Tag(
                name="child1-child1",
                data="c1-c1 Hello",
                parent_id=child1.id,
                tree_id=tree.id,
                order=0,
            ),
            Tag(
                name="child1-child2",
                data="c1-c2 JS",
                parent_id=child1.id,
                tree_id=tree.id,
                order=1,
            ),
        ]
    )

    db.commit()
    print("Database seeded successfully.")
