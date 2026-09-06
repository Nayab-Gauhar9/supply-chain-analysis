import time
import logging
import src.logging_config
import re
from pathlib import Path
from src.database.connection import get_pool
from src.database.exceptions import MigrationExecutionError

logger = logging.getLogger(__name__)
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

def ensure_migration_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            migration_name TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

def get_migrations():
    migrations = []

    for path in MIGRATIONS_DIR.glob("*.sql"):
        match = re.match(r"^(\d+)_(.+)\.sql$", path.name)

        if not match:
            continue

        version = int(match.group(1))
        name = match.group(2)

        migrations.append((version, name, path))

    return sorted(migrations, key=lambda migration: migration[0])

def get_applied_migrations(conn):
    rows = conn.execute("""
        SELECT version
        FROM schema_migrations
        ORDER BY version;
    """).fetchall()

    return {row[0] for row in rows}

def apply_migration(conn, version, name, path):
    try:
        sql = path.read_text(encoding="utf-8")

        conn.execute(sql)

        conn.execute(
            """
            INSERT INTO schema_migrations (version, migration_name)
            VALUES (%s, %s);
            """,
            (version, name),
        )
    except Exception as e:
        raise MigrationExecutionError(f"Failed to apply migration {version}: {name}") from e


def run_migrations():
    run_start_time = time.perf_counter()
    pool = get_pool()
    try:
        with pool.connection() as conn:
    
            ensure_migration_table(conn)

            applied_migrations = get_applied_migrations(conn)
            migrations = get_migrations()
            logger.info(f"migration_run_started | total_migrations = {len(migrations)} | already_applied = {len(applied_migrations)}")
            applied_count = 0
            skipped_count = 0

            for version, name, path in migrations:
                if version in applied_migrations:
                    skipped_count += 1
                    logger.info(f"migration_skipped | version = {version} | migration_name = {name}")
                    continue
                migration_start_time = time.perf_counter()
                try:
                    logger.info(f"migration_started | version = {version} | migration_name = {name}")
                    apply_migration(conn, version, name, path)
                    conn.commit()
                    migration_duration_ms = (time.perf_counter() - migration_start_time) * 1000
                    applied_count += 1
                    logger.info(f"migration_completed | version = {version} | migration_name = {name} | duration_ms = {migration_duration_ms}")
                except Exception:
                    conn.rollback()
                    migration_duration_ms = (time.perf_counter() - migration_start_time) * 1000
                    logger.exception(f"migration_failed | version = {version} | migration_name = {name} | duration_ms = {migration_duration_ms}")
                    raise
            run_duration_ms = (time.perf_counter() - run_start_time)* 1000
            logger.info(f"migration_run_completed | total_migrations = {len(migrations)} | applied = {applied_count} | skipped = {skipped_count} | duration_ms = {run_duration_ms:.2f}")
    except Exception:
            logger.exception("migration_runner_failed")
            raise

if __name__=="__main__":
    run_migrations()