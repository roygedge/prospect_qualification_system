from sqlalchemy import Column, String, Boolean, Integer, Index, UniqueConstraint, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Prospect(Base):
    """Model for a prospect in the database"""
    __tablename__ = "prospects"

    MAX_LENGTH_COUNTRY = 10
    MAX_LENGTH_STATE = 10
    MAX_LENGTH_USER_ID = 255
    MAX_LENGTH_PROSPECT_ID = 255

    id = Column(Integer, primary_key=True)
    user_id = Column(String(MAX_LENGTH_USER_ID), nullable=False)
    prospect_id = Column(String(MAX_LENGTH_PROSPECT_ID), nullable=False)
    company_country = Column(String(MAX_LENGTH_COUNTRY), nullable=False)
    company_state = Column(String(MAX_LENGTH_STATE))
    qualified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Add indexes for better performance
    __table_args__ = (
        Index('idx_user_prospect', user_id, prospect_id),
        Index('idx_qualified', qualified),
        UniqueConstraint('user_id', 'prospect_id', name='uq_user_prospect'),
    )

    def __init__(self, user_id: str, prospect_id: str, company_country: str, 
                 company_state: str = None, qualified: bool = False):
        self.user_id = user_id
        self.prospect_id = prospect_id
        self.company_country = company_country
        self.company_state = company_state
        self.qualified = qualified

    def to_dict(self):
        """Convert the prospect to a dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'prospect_id': self.prospect_id,
            'company_country': self.company_country,
            'company_state': self.company_state,
            'qualified': self.qualified,
            'created_at': self.created_at,
            'last_updated': self.last_updated
        }