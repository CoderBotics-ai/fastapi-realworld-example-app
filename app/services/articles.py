from slugify import slugify

from app.db.errors import EntityDoesNotExist
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient("mongodb://localhost:27017/")


def check_user_can_modify_article(article: Article, user: User) -> bool:
    client = MongoClient()
    db = client['your_database_name']
    articles_collection = db['articles']
    users_collection = db['users']

    article_data = articles_collection.find_one({"_id": ObjectId(article.id)})
    if not article_data:
        raise EntityDoesNotExist("Article does not exist")

    author_data = users_collection.find_one({"_id": article_data['author_id']})
    if not author_data:
        raise EntityDoesNotExist("Author does not exist")

    return author_data['username'] == user.username
db = client["your_database_name"]
articles_collection = db["articles"]


def get_slug_for_article(title: str) -> str:
    slug = slugify(title)
    if articles_collection.find_one({"slug": slug}):
        raise EntityDoesNotExist(f"Article with slug '{slug}' already exists.")
    return slug


async def check_article_exists(articles_repo: ArticlesRepository, slug: str) -> bool:
    client = MongoClient()
    db = client['your_database_name']
    articles_collection = db['articles']

    article = await articles_collection.find_one({"slug": slug})
    client.close()

    if article is None:
        return False

    return True
