from slugify import slugify

from app.db.errors import EntityDoesNotExist
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User

from pymongo.results import InsertOneResult, InsertManyResult, DeleteResult, UpdateResult
from pymongo.collection import Collection
from app.db.repositories.base import BaseRepository

def check_user_can_modify_article(article: Article, user: User) -> bool:
    """Checks if a user can modify an article."""
    return article.author.username == user.username

def get_slug_for_article(title: str) -> str:
    """Returns a slug for the given article title."""
    return slugify(title)

async def check_article_exists(articles_repo: ArticlesRepository, slug: str) -> bool:
    """Checks if an article exists in the database."""
    article = await articles_repo.collection.find_one({"slug": slug})
    return article is not None
