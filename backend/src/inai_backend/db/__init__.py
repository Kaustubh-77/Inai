"""Persistence layer: ORM models and database helpers.

The Alembic migrations in ``backend/migrations`` are the source of truth for the schema,
including CHECK constraints, triggers, partial indexes and composite ownership keys.
The ORM models mirror the tables and columns; a test checks that they stay in step.
"""
