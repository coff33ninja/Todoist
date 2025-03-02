import sqlite3
import time
from typing import Optional, List, Dict, Any
from .error_logger import ErrorLogger


class DatabaseError(Exception):
    """Custom exception for database-related errors.

    Attributes:
        message (str): Explanation of the error
        error_code (int, optional): Error code associated with the database error
        query (str, optional): SQL query that caused the error
        original_exception (Exception, optional): The original exception caught
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        query: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.query = query
        self.original_exception = original_exception

        detailed_message = f"{message}"
        if error_code is not None:
            detailed_message += f" (Error code: {error_code})"
        if query is not None:
            detailed_message += f"\nQuery: {query}"
        if original_exception is not None:
            detailed_message += f"\nOriginal error: {str(original_exception)}"

        super().__init__(detailed_message)


class DatabaseHandler:
    def __init__(self, db_path: str, max_retries: int = 3, retry_delay: int = 1):
        """Initialize the DatabaseHandler.

        Args:
            db_path (str): Path to the SQLite database file
            max_retries (int, optional): Maximum number of retry attempts for operations
            retry_delay (int, optional): Delay in seconds between retries
        """
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_logger = ErrorLogger()

    def _connect(self) -> sqlite3.Connection:
        """Establish a new database connection.

        Returns:
            sqlite3.Connection: A new database connection

        Raises:
            DatabaseError: If connection fails
        """
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            self.error_logger.log_error("Failed to connect to database", e)
            raise DatabaseError(
                message="Failed to connect to database", original_exception=e
            )

    def get_database_cursor(self, db_conn=None) -> sqlite3.Cursor:
        """Get a database cursor with retry mechanism.

        Args:
            db_conn (callable or sqlite3.Connection, optional): Connection or connection factory

        Returns:
            sqlite3.Cursor: A cursor for database operations

        Raises:
            DatabaseError: If cursor retrieval fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                if db_conn:
                    if callable(db_conn):
                        conn = db_conn()
                    else:
                        conn = db_conn
                    return conn.cursor()
                return self._connect().cursor()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    self.error_logger.log_error(
                        f"Database connection failed after {self.max_retries} attempts",
                        e,
                    )
                    raise DatabaseError(
                        message="Database connection failed", original_exception=e
                    )
                time.sleep(self.retry_delay)

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        commit: bool = False,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[List[tuple]]:
        """Execute a single SQL query.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            commit (bool, optional): Whether to commit the transaction
            conn (sqlite3.Connection, optional): Existing connection to use

        Returns:
            list: Query results if any, None for non-SELECT queries

        Raises:
            DatabaseError: If query execution fails
        """
        close_conn = False
        if conn is None:
            conn = self._connect()
            close_conn = True

        cursor = None
        try:
            cursor = conn.cursor()

            for attempt in range(self.max_retries):
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    break
                except sqlite3.OperationalError as e:
                    if (
                        "database is locked" in str(e)
                        and attempt < self.max_retries - 1
                    ):
                        time.sleep(self.retry_delay)
                    else:
                        raise
                except sqlite3.Error:
                    raise

            if commit:
                conn.commit()

            return cursor.fetchall() if cursor.description else None

        except sqlite3.Error as e:
            if commit and close_conn:
                conn.rollback()
            error_code = e.sqlite_errorcode if hasattr(e, "sqlite_errorcode") else None
            self.error_logger.log_error(f"Query execution failed: {query}", e)
            raise DatabaseError(
                message="Query execution failed",
                error_code=error_code,
                query=query,
                original_exception=e,
            )
        finally:
            if cursor:
                cursor.close()
            if close_conn:
                conn.close()

    def execute_transaction(
        self, queries: List[Dict[str, Any]], conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Execute multiple queries as a single transaction.

        Args:
            queries (list): List of dicts with 'query' and optional 'params' keys
            conn (sqlite3.Connection, optional): Existing connection to use

        Returns:
            bool: True if transaction succeeds

        Raises:
            ValueError: If queries list is malformed
            DatabaseError: If transaction fails
        """
        if not all(isinstance(q, dict) and "query" in q for q in queries):
            raise ValueError("Each query must be a dictionary with a 'query' key")

        close_conn = False
        if conn is None:
            conn = self._connect()
            close_conn = True

        cursor = None
        current_query = None
        try:
            cursor = conn.cursor()

            for query_data in queries:
                current_query = query_data["query"]
                params = query_data.get("params")
                for attempt in range(self.max_retries):
                    try:
                        if params:
                            cursor.execute(current_query, params)
                        else:
                            cursor.execute(current_query)
                        break
                    except sqlite3.OperationalError as e:
                        if (
                            "database is locked" in str(e)
                            and attempt < self.max_retries - 1
                        ):
                            time.sleep(self.retry_delay)
                        else:
                            raise
                    except sqlite3.Error:
                        raise

            if close_conn:
                conn.commit()
            return True

        except sqlite3.Error as e:
            if close_conn:
                conn.rollback()
            error_code = e.sqlite_errorcode if hasattr(e, "sqlite_errorcode") else None
            self.error_logger.log_error(
                f"Query failed in transaction: {current_query}", e
            )
            raise DatabaseError(
                message="Query failed in transaction",
                error_code=error_code,
                query=current_query,
                original_exception=e,
            )
        finally:
            if cursor:
                cursor.close()
            if close_conn:
                conn.close()
