from app.models.domain.comments import Comment
from app.models.domain.users import User

from bson.objectid import ObjectId
from pymongo.collection import Collection

def check_user_can_modify_comment(comment: dict, user: dict) -> bool:
    """Checks if a user can modify a comment."""
    return comment['author_id'] == user['_id']
