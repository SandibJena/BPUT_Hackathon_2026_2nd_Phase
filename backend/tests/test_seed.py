from PIL import Image
from sqlalchemy import func, inspect, select

from app.core.database import session_factory
from app.models.entities import AuditLog, ConsentRecord, Patient, TriageNoteRecord, User
from app.seed import seed
from app.services.audit import verify_integrity


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_seed_is_idempotent_and_does_not_fabricate_notes(engine, tmp_path):
    assets = tmp_path / 'synthetic'
    assert seed(engine, asset_dir=assets) == 25
    assert seed(engine, asset_dir=assets) == 0
    with session_factory(engine)() as session:
        assert count(session, Patient) == 25
        assert count(session, ConsentRecord) == 25
        assert count(session, User) == 4
        assert count(session, TriageNoteRecord) == 0
        assert count(session, AuditLog) == 56  # 4 users + 50 consent/patient events + 2 asset generations
        assert all(c.accepted and c.synthetic for c in session.scalars(select(ConsentRecord)))
        assert verify_integrity(session)
    assert len(list((assets / 'reports').glob('*.png'))) == 5
    assert len(list((assets / 'reports').glob('*.pdf'))) == 5
    assert len(list((assets / 'images').glob('*.png'))) == 3
    for image_path in (assets / 'images').glob('*.png'):
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            assert not image.getexif()
    for pdf in (assets / 'reports').glob('*.pdf'):
        assert pdf.read_bytes().startswith(b'%PDF')


def test_required_tables_exist(engine):
    assert set(inspect(engine).get_table_names()) == {
        'users', 'patients', 'triage_notes', 'uploads', 'audit_log', 'consent_records',
    }
