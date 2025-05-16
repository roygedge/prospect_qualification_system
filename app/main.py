from fastapi import FastAPI
from app.services.prospect_service import ProspectService
from app.repositories.prospect_repository import ProspectRepository

app = FastAPI()

# Initialize repositories
prospect_repository = ProspectRepository()

# Initialize services
prospect_service = ProspectService(prospect_repository)


@app.get("/qualify")
def get_qualified_prospects():
    processed_count = prospect_service.qualify_prospects()
    qualified_prospects = prospect_repository.get_qualified_prospects()
    
    return {
        "total_processed": processed_count,
        "qualified": len(qualified_prospects),
        "not_qualified": processed_count - len(qualified_prospects),
    }

@app.get("/")
def root():
    return {"message": "Welcome to the Prospect Qualification API"}
