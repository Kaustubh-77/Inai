"""Migration history checks that need no database (T1.2)."""

from alembic.config import Config
from alembic.script import ScriptDirectory

from tests.db.support import BACKEND_DIR


def _scripts() -> ScriptDirectory:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    return ScriptDirectory.from_config(cfg)


def test_single_linear_history_starting_at_initial_schema() -> None:
    scripts = _scripts()
    assert len(scripts.get_heads()) == 1
    revisions = list(scripts.walk_revisions())
    assert revisions[-1].revision == "0001_initial_schema"
    assert revisions[-1].down_revision is None
