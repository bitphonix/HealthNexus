# seed_db.py
from backend.services.seeder import seed_all
from backend.database import SessionLocal, init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    init_db() 
    db = SessionLocal()
    try:
        seed_all(db)
    except Exception as e:
        logger.error(f"An error occurred during seeding: {e}")
    finally:
        db.close()