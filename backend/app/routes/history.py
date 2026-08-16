"""
History routes: list and delete per-user operation history.
Ownership is enforced at the query level (user_id filter), not just the UI.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, HistoryEntry
from app.services.auth_service import get_current_user

logger = logging.getLogger("quickmind.history")
router = APIRouter(prefix="/api", tags=["History"])


@router.get("/history")
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's history entries, newest first."""
    entries = (
        db.query(HistoryEntry)
        .filter(HistoryEntry.user_id == current_user.id)
        .order_by(HistoryEntry.created_at.desc())
        .all()
    )
    return {
        "success": True,
        "data": [
            {
                "id": e.id,
                "operation_type": e.operation_type,
                "input_summary": e.input_summary,
                "result": e.result,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ],
    }


@router.delete("/history/{entry_id}")
def delete_history_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a single history entry. Users can only delete their own entries."""
    entry = (
        db.query(HistoryEntry)
        .filter(HistoryEntry.id == entry_id, HistoryEntry.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History entry not found.",
        )
    db.delete(entry)
    db.commit()
    return {"success": True, "message": "History entry deleted."}
