from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.template import Context, Engine


ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = ROOT / "afritech/apps/afroprog/dashboard/templates"


def _ensure_settings() -> None:
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            SECRET_KEY="afroprog-test-key",
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [str(TEMPLATE_DIR)],
                    "APP_DIRS": False,
                }
            ],
        )


def test_django_runtime_can_render_afroprog_dashboard_template() -> None:
    _ensure_settings()
    engine = Engine(dirs=[str(TEMPLATE_DIR)])
    template = engine.get_template("dashboard.html")
    rendered = template.render(Context({}))

    assert "AfriPro Dashboard" in rendered
    assert "Project Explorer" in rendered
    assert "Chat / AI Assistant Panel" in rendered
    assert "Code Editor" in rendered


def test_django_runtime_template_path_exists() -> None:
    assert TEMPLATE_DIR.exists()
    assert (TEMPLATE_DIR / "dashboard.html").exists()
