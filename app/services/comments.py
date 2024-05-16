from app.models.domain.comments import Comment
from app.models.domain.users import User
from bson import ObjectId
from pymongo.collection import Collection


from pymongo import MongoClient


def check_user_can_modify_comment(comment: Comment, user: User) -> bool:
    comments_collection: Collection = db.get_collection("comments")
    users_collection: Collection = db.get_collection("users")

    comment_data = comments_collection.find_one({"_id": ObjectId(comment.comment_id)})
    user_data = users_collection.find_one({"_id": ObjectId(user.user_id)})

    if comment_data and user_data:
        return comment_data["author_id"] == user_data["_id"]
    return False
