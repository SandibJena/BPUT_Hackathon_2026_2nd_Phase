from fastapi import APIRouter, Request
from sqlalchemy import text

from app.core.config import DISCLAIMER

router = APIRouter()


@router.get('/health')
def health(request: Request):
    with request.app.state.engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    return {
        'status': 'ok', 'phase': 1, 'synthetic_only': True,
        'processing_enabled': False, 'disclaimer': DISCLAIMER,
    }
