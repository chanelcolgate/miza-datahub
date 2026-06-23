import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import CursorResult

logger = logging.getLogger(__name__)


class PostgresRepository:
    """
    PostgreSQL repository using SQLAlchemy ORM for executing queries and
    managing connections.
    Similar to InfluxRepository but for PostgreSQL database with SQLAlchemy.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        pool_size: int = 10,
        max_overflow: int = 20,
    ):
        """
        Initialize PostgreSQL repository.

        Args:
            host: Database host
            port: Database port (default 5432)
            database: Database name
            username: Database username
            password: Database password
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
        """
        # Create SQLAlchemy engine with psycopg[binary]
        connection_string = (
            f"postgresql+psycopg://{username}:{password}"
            f"@{host}:{port}/{database}"
        )

        self.engine = create_engine(
            connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
            pool_pre_ping=True,  # Verify connections before using them
        )

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        logger.info(f"PostgreSQL engine created: {host}:{port}/{database}")

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()

    def query(
        self, sql: str, params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Execture SELECT query and return results as list of dictionaries.

        Args:
            sql: SQL query string (can use :param_name for parameters)
            params: Optional dictionary of parameters

        Returns:
            List of dictionaries containing query results
        """
        session = self.get_session()
        try:
            result = session.execute(text(sql), params or {})
            rows = result.fetchall()

            # Convert Row objects to dictionaries
            return [dict(row._mapping) for row in rows]

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            session.close()

    def query_one(
        self, sql: str, params: Dict[str, Any] | None = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute SELECT query and return first result.

        Args:
            sql: SQL query string
            params: Optional dictionary of parameters

        Returns:
            Dictionary of first row or None if no results
        """
        results = self.query(sql, params)
        return results[0] if results else None

    def execute(self, sql: str, params: Dict[str, Any] | None = None) -> int:
        """
        Execute INSERT/UPDATE/DELETE query.

        Args:
            sql: SQL statement string
            params: Optional dictionary of parameters

        Returns:
            Number of affected rows
        """
        session = self.get_session()
        try:
            result = session.execute(text(sql), params or {})
            session.commit()

            cursor_result: CursorResult = result  # type: ignore[assignment]

            affected_rows = cursor_result.rowcount
            logger.info(f"Execute statement affected {affected_rows} rows")
            return affected_rows
        except Exception as e:
            session.rollback()
            logger.error(f"Execute failed: {e}")
            raise
        finally:
            session.close()

    def execute_many(self, sql: str, data: List[Dict[str, Any]]) -> int:
        """
        Execute INSERT/UPDATE/DELETE for multiple records efficiently.

        Args:
            sql: SQL statement template with :param_name placeholders
            data: List of dictionaries with parameters for each execution

        Returns:
            Total number of affected rows
        """
        session = self.get_session()
        total_rows = 0

        try:
            for params in data:
                result = session.execute(text(sql), params)

                cursor_result: CursorResult = result  # type: ignore[assignment]

                total_rows += cursor_result.rowcount

            session.commit()
            logger.info(f"Execute many affected {total_rows} total rows")
            return total_rows
        except Exception as e:
            session.rollback()
            logger.error(f"Execute many failed: {e}")
            raise  # type: ignore[return]
        finally:
            session.close()

    def get_health(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def dispose(self) -> None:
        """
        Dispose all connections in the pool.
        Should be called before application shutdown.
        """
        self.engine.dispose()
        logger.info("Connection pool disposed")
