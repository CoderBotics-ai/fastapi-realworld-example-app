from slugify import slugify

from app.db.errors import EntityDoesNotExist
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from bson.objectid import ObjectId
from pymongo.collection import Collection


async def check_article_exists(articles_repo: ArticlesRepository, slug: str) -> bool:
    collection: Collection = articles_repo.collection  # Assuming articles_repo has a pymongo collection attribute
    article = await collection.find_one({"slug": slug})
    if article is None:
        return False
    return True


def check_user_can_modify_article(article: Article, user: User) -> bool:
    return article.author.username == user.username


def get_slug_for_article(title: str) -> str:
    return slugify(title)
