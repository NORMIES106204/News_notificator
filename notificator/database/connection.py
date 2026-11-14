
import os
import psycopg
import traceback

from dotenv import load_dotenv


class DatabaseConnection:
    def __init__(self):
        load_dotenv()

        self.connection = None

        self.config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "connect_timeout": int(
                os.getenv("DB_CONNECT_TIMEOUT", "5")
            ),
        }

    def connect(self):
        """Establish a PostgreSQL connection."""

        try:
            # Avoid creating duplicate connections
            if self.is_connected():
                print("[DATABASE] Already connected.")
                return True

            self.connection = psycopg.connect(
                **self.config,
                autocommit=True
            )

            print("[DATABASE] Connection established.")
            return True

        except Exception:
            print("[DATABASE] Connection failed!")
            traceback.print_exc()

            self.connection = None
            return False

    def is_connected(self):
        """Check whether the local connection object is open."""

        return (
            self.connection is not None
            and not self.connection.closed
        )

    def check_connection(self):
        """
        Check whether PostgreSQL is actually responding.

        SELECT 1 does not read or modify application data.
        """

        if not self.is_connected():
            print("[DATABASE] No active connection.")
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            if result == (1,):
                print("[DATABASE] Server is reachable.")
                return True

            print("[DATABASE] Unexpected health-check result.")
            return False

        except Exception:
            print("[DATABASE] Health check failed!")
            traceback.print_exc()
            return False

    def close(self):
        """Close the database connection safely."""

        try:
            if self.is_connected():
                self.connection.close()
                print("[DATABASE] Connection closed.")
            else:
                print("[DATABASE] No connection to close.")

        except Exception:
            print("[DATABASE] Error while closing connection!")
            traceback.print_exc()

        finally:
            self.connection = None

    def reconnect(self):
        """Close the old connection and establish a new one."""

        print("[DATABASE] Reconnecting...")

        self.close()
        return self.connect()
