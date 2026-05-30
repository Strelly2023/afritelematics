from __future__ import annotations

import os

import pytest


_DJANGO_TABLES_READY = False


def pytest_configure() -> None:
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "afriride_system.django_app.config.settings",
    )

    try:
        import django
        from django.apps import apps
    except ModuleNotFoundError:
        return

    if not apps.ready:
        django.setup()

    _ensure_django_tables()


def _ensure_django_tables() -> None:
    global _DJANGO_TABLES_READY

    if _DJANGO_TABLES_READY:
        return

    try:
        from django.apps import apps
        from django.db import connection
    except ModuleNotFoundError:
        return

    existing_tables = set(connection.introspection.table_names())

    with connection.schema_editor() as schema:
        for model in apps.get_models():
            if model._meta.db_table in existing_tables:
                continue
            schema.create_model(model)
            existing_tables.add(model._meta.db_table)

    _DJANGO_TABLES_READY = True


def _clear_django_tables() -> None:
    try:
        from django.apps import apps
        from django.db import DatabaseError, connection
    except ModuleNotFoundError:
        return

    connection.disable_constraint_checking()
    try:
        for model in reversed(apps.get_models()):
            try:
                model.objects.all().delete()
            except DatabaseError:
                continue
    finally:
        connection.enable_constraint_checking()


@pytest.fixture(autouse=True)
def _django_db_marker_compat(request: pytest.FixtureRequest):
    if request.node.get_closest_marker("django_db") is None:
        yield
        return

    _ensure_django_tables()
    _clear_django_tables()
    yield
    _clear_django_tables()
