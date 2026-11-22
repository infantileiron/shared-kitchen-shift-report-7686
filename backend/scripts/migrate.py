from pathlib import Path

from src.models.db import connect


def main():
    with connect() as db:
        db.execute('SELECT pg_advisory_xact_lock(521300)')
        for migration in sorted(Path('migrations').glob('*.sql')):
            db.execute(migration.read_text())


if __name__ == '__main__':
    main()
