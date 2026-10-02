from collections.abc import Sequence

from src.database.connection import get_connection
from src.models.article import Article


class ArticleRepository:
    """Read-only repository for articles."""

    def get_unprocessed_articles(self) -> list[Article]:
        """
        Return all articles that have not been processed.

        This method only reads from the database.
        """
        query = """
            SELECT
                id,
                source_id,
                feed_id,
                title,
                description,
                url,
                published_at,
                collected_at,
                language,
                processed
            FROM articles
            WHERE processed = FALSE
            ORDER BY collected_at ASC;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

        return [self._row_to_article(row) for row in rows]

    @staticmethod
    def _row_to_article(row: Sequence) -> Article:
        """Convert one database row into an Article model."""
        return Article(
            id=row[0],
            source_id=row[1],
            feed_id=row[2],
            title=row[3],
            description=row[4],
            url=row[5],
            published_at=row[6],
            collected_at=row[7],
            language=row[8],
            processed=row[9],
        )