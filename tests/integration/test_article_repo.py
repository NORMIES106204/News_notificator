from src.models.article import Article
from src.repositories.article_repo import ArticleRepository


def test_get_unprocessed_articles():
    repository = ArticleRepository()

    articles = repository.get_unprocessed_articles()

    assert isinstance(articles, list)

    for article in articles:
        assert isinstance(article, Article)
        assert article.processed is False

    print(f"\nFound {len(articles)} unprocessed article(s).")

    for article in articles[:5]:
        print("\n--- Article ---")
        print(f"ID:          {article.id}")
        print(f"Title:       {article.title}")
        print(f"Source ID:   {article.source_id}")
        print(f"Feed ID:     {article.feed_id}")
        print(f"URL:         {article.url}")
        print(f"Published:   {article.published_at}")
        print(f"Collected:   {article.collected_at}")
        print(f"Language:    {article.language}")
        print(f"Processed:   {article.processed}")