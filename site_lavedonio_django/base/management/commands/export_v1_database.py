"""
Copies, from the v1 PostgreSQL database, the tables that import_v1_content
reads into a local SQLite file, so the import can be tested (and re-run) without
touching the v1 database:

    python manage.py export_v1_database --url-file ../postgres_conn.txt
    python manage.py import_v1_content ../v1_export/v1.sqlite3 --dry-run

The connection is read-only and only the columns used by the import are copied
(e.g. no password hashes from auth_user).
"""
import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from .import_v1_content import V1_OPTIONAL_COLUMNS, V1_OPTIONAL_TABLES, V1_TABLES


def to_sqlite(value):
    # Dates are stored as ISO 8601 text, which import_v1_content parses (with the UTC offset)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


class Command(BaseCommand):
    help = 'Copies the v1 tables needed by import_v1_content from PostgreSQL to a local SQLite file (read-only).'

    def add_arguments(self, parser):
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument('--url', help='PostgreSQL URL of the v1 database (postgres://user:password@host:port/name).')
        source.add_argument('--url-file', type=Path, help='File whose first line is the PostgreSQL URL of the v1 database.')
        parser.add_argument(
            '--output', type=Path, default=Path(settings.BASE_DIR) / 'v1_export' / 'v1.sqlite3',
            help='SQLite file to create (replaced if it exists). Defaults to <BASE_DIR>/v1_export/v1.sqlite3.',
        )

    def handle(self, *args, **options):
        try:
            import psycopg2
        except ImportError as error:
            raise CommandError('psycopg2 is needed to read the v1 database.') from error

        url = options['url'] or self.read_url(options['url_file'])
        output = options['output']
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + '.tmp')
        temporary.unlink(missing_ok=True)

        try:
            # Heroku Postgres only accepts SSL connections
            source = psycopg2.connect(url, sslmode='require', connect_timeout=15)
        except psycopg2.Error as error:
            raise CommandError(f'Could not connect to the v1 database: {error}') from error

        with closing(source), closing(sqlite3.connect(temporary)) as target:
            source.set_session(readonly=True)
            tables = dict(V1_TABLES)
            with source.cursor() as cursor:
                for table, required in V1_OPTIONAL_TABLES.items():
                    cursor.execute('SELECT 1 FROM information_schema.tables WHERE table_name = %s', [table])
                    if cursor.fetchone():
                        tables[table] = required

            for table, required in tables.items():
                with source.cursor() as cursor:
                    cursor.execute(f'SELECT * FROM "{table}" LIMIT 0')
                    available = {column.name for column in cursor.description}
                    columns = sorted(required | (V1_OPTIONAL_COLUMNS.get(table, set()) & available))
                    quoted = ', '.join(f'"{column}"' for column in columns)

                    cursor.execute(f'SELECT {quoted} FROM "{table}"')
                    rows = [tuple(to_sqlite(value) for value in row) for row in cursor.fetchall()]

                target.execute(f'CREATE TABLE "{table}" ({quoted})')
                target.executemany(f'INSERT INTO "{table}" ({quoted}) VALUES ({", ".join("?" * len(columns))})', rows)
                self.stdout.write(f'{table}: {len(rows)} rows')
            target.commit()

        temporary.replace(output)
        self.stdout.write(self.style.SUCCESS(f'Saved to {output}'))

    def read_url(self, path):
        try:
            return path.read_text().strip().splitlines()[0].strip()
        except (OSError, IndexError) as error:
            raise CommandError(f'Could not read the database URL from {path}.') from error
