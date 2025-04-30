from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg2 import OperationalError as psycopg20pError
from time import sleep


class Command(BaseCommand):
    """Django command to wait for database."""
    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        db_up = False
        while not db_up:
            try:
                self.check(databases=["default"])
                db_up = True
            except (OperationalError, psycopg20pError):
                self.stdout.write("Database unavailable, wait 1 seconds...")
                sleep(1)
        self.stdout.write(self.style.SUCCESS("Database available."))
