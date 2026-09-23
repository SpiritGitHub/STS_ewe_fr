from __future__ import annotations

from fastapi import APIRouter

from ..services.context import get_context
from ..models.db_models import list_history

router = APIRouter(tags=["history"])


@router.get("/api/history")
def history(limit: int = 50) -> dict:
    ctx = get_context()
    items = list_history(ctx.db_path, limit=limit)
    return {
        "count": len(items),
        "items": [
            {
                "id": it.id,
                "created_at": it.created_at,
                "direction": it.direction,
                "kind": it.kind,
                "input_text": it.input_text,
                "output_text": it.output_text,
                "meta_json": it.meta_json,
            }
            for it in items
        ],
    }
