from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.progress import SearchResponse
from app.services.search import search_learning


router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(default=""), db: Session = Depends(get_db)) -> dict:
    return search_learning(db, q)
