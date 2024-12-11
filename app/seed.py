from database import SessionLocal, engine
from models import Base
from utils.seeder import seed_data

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# Seed the database
db = SessionLocal()
try:
    seed_data(db)
finally:
    db.close()
