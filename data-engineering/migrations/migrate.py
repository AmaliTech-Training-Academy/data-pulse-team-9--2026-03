import os
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text

MIGRATIONS_DIR = Path(__file__).parent
STATE_FILE = MIGRATIONS_DIR / ".migration_state.json"


def get_connection_string():
    return os.getenv(
        "TARGET_DB_URL",
        "postgresql://datapulse:datapulse@localhost:5432/datapulse"
    )


def get_applied_migrations() -> list:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f).get("applied", [])
    return []


def save_migration_state(applied: list):
    with open(STATE_FILE, "w") as f:
        json.dump({"applied": applied, "last_run": datetime.now().isoformat()}, f, indent=2)


def get_pending_migrations() -> list:
    applied = set(get_applied_migrations())
    all_migrations = sorted([
        f.stem for f in MIGRATIONS_DIR.glob("V*.py")
        if f.stem not in applied and f.name != "__init__.py"
    ])
    return all_migrations


def run_migration(migration_name: str, engine):
    module = __import__(migration_name)
    
    print(f"Running migration: {migration_name}")
    
    if hasattr(module, "upgrade"):
        with engine.begin() as conn:
            module.upgrade(conn)
        print(f"  Completed: {migration_name}")
        return True
    else:
        print(f"  Skipped: {migration_name} (no upgrade function)")
        return False


def rollback_migration(migration_name: str, engine):
    module = __import__(migration_name)
    
    print(f"Rolling back: {migration_name}")
    
    if hasattr(module, "downgrade"):
        with engine.begin() as conn:
            module.downgrade(conn)
        print(f"  Rolled back: {migration_name}")
        return True
    else:
        print(f"  Cannot rollback: {migration_name} (no downgrade function)")
        return False


def migrate():
    engine = create_engine(get_connection_string())
    pending = get_pending_migrations()
    
    if not pending:
        print("No pending migrations.")
        return
    
    print(f"Found {len(pending)} pending migration(s)")
    applied = get_applied_migrations()
    
    for migration in pending:
        try:
            if run_migration(migration, engine):
                applied.append(migration)
                save_migration_state(applied)
        except Exception as e:
            print(f"Migration failed: {migration}")
            print(f"Error: {e}")
            break
    
    print(f"Applied {len(applied)} migration(s)")


def rollback(steps: int = 1):
    engine = create_engine(get_connection_string())
    applied = get_applied_migrations()
    
    if not applied:
        print("No migrations to rollback.")
        return
    
    to_rollback = applied[-steps:]
    
    for migration in reversed(to_rollback):
        try:
            if rollback_migration(migration, engine):
                applied.remove(migration)
                save_migration_state(applied)
        except Exception as e:
            print(f"Rollback failed: {migration}")
            print(f"Error: {e}")
            break


def status():
    applied = get_applied_migrations()
    pending = get_pending_migrations()
    
    print("Migration Status")
    print("-" * 40)
    print(f"Applied: {len(applied)}")
    for m in applied:
        print(f"  [x] {m}")
    print(f"Pending: {len(pending)}")
    for m in pending:
        print(f"  [ ] {m}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        status()
    elif sys.argv[1] == "migrate":
        migrate()
    elif sys.argv[1] == "rollback":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        rollback(steps)
    elif sys.argv[1] == "status":
        status()
    else:
        print("Usage: python migrate.py [migrate|rollback|status]")
