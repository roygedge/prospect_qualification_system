from typing import List, Iterator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.models.prospect import Prospect, Base
from app.config import PROSPECT_DB, PROSPECT_USER, PROSPECT_PASSWORD, PROSPECT_DB_HOST, PROSPECT_DB_PORT

class ProspectRepository:
    """Repository for prospect"""

    DEFAULT_BATCH_SIZE = 1000

    def __init__(self):
        DATABASE_URL = f"postgresql://{PROSPECT_USER}:{PROSPECT_PASSWORD}@{PROSPECT_DB_HOST}:{PROSPECT_DB_PORT}/{PROSPECT_DB}"
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        # Drop all tables (for testing/dev purposes)
        # Base.metadata.drop_all(bind=self.engine) 
        Base.metadata.create_all(bind=self.engine)
        
        # Create indexes for better performance
        self._create_indexes()

    def _create_indexes(self):
        """Create optimized indexes if they don't exist"""
        with self.engine.connect() as connection:
            # Index for fast qualification status lookup
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_prospects_qualified 
                ON prospects (qualified) 
                WHERE qualified = true;
                
                -- Composite index for efficient user_id + prospect_id lookups
                CREATE INDEX IF NOT EXISTS idx_prospects_user_prospect 
                ON prospects (user_id, prospect_id);
            """))

            # Placeholder for any other indexes
            
            connection.commit()

    @contextmanager
    def get_session(self):
        """Get the session for the database"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def get_qualified_prospects(self, batch_size: int = DEFAULT_BATCH_SIZE):
        """Get qualified prospects from the database by batches"""
        with self.get_session() as session:
            query = session.query(Prospect)\
                .filter(Prospect.qualified.is_(True))\
                .yield_per(batch_size)
            
            # Convert to list of dicts for consistency with current implementation
            return [prospect.to_dict() for prospect in query]

    def _chunk_prospects(self, prospects: List[Prospect], chunk_size: int) -> Iterator[List[Prospect]]:
        """Split prospects into chunks for batch processing"""
        for i in range(0, len(prospects), chunk_size):
            yield prospects[i:i + chunk_size]

    def add_prospects(self, prospects: List[Prospect], batch_size: int = DEFAULT_BATCH_SIZE):
        """Add multiple prospects using efficient batching and PostgreSQL's UPSERT"""
        if not prospects:
            return

        with self.get_session() as session:
            # Process prospects in batches
            for prospect_batch in self._chunk_prospects(prospects, batch_size):
                # Extract IDs for current batch
                user_ids = [p.user_id for p in prospect_batch]
                prospect_ids = [p.prospect_id for p in prospect_batch]

                # Get existing prospects for this batch
                existing_map = {
                    (p.user_id, p.prospect_id): p 
                    for p in session.query(Prospect).filter(
                        Prospect.user_id.in_(user_ids),
                        Prospect.prospect_id.in_(prospect_ids)
                    ).with_for_update().all()
                }

                # Prepare batch inserts and updates
                new_prospects = []
                updates = []

                for prospect in prospect_batch:
                    key = (prospect.user_id, prospect.prospect_id)
                    if key in existing_map:
                        existing = existing_map[key]
                        updates.append({
                            'id': existing.id,
                            'company_country': prospect.company_country,
                            'company_state': prospect.company_state,
                            'qualified': prospect.qualified
                        })
                    else:
                        new_prospects.append(prospect)

                # Bulk insert new prospects
                if new_prospects:
                    session.bulk_save_objects(new_prospects)

                # Bulk update existing prospects
                if updates:
                    statement = text("""
                        UPDATE prospects 
                        SET 
                            company_country = :company_country,
                            company_state = :company_state,
                            qualified = :qualified
                        WHERE id = :id
                    """)
                    session.execute(statement, updates)

                # Commit each batch
                session.commit()
