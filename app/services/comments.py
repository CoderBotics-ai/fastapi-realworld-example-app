from app.models.domain.comments import Comment
from app.models.domain.users import User
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client["your_database_name"]
users_collection = db["users"]


def check_user_can_modify_comment(comment: Comment, user: User) -> bool:
    user_data = users_collection.find_one({"username": user.username})
    if user_data:
        for user_comment in user_data.get("comments", []):
            if user_comment["comment_id"] == ObjectId(comment.id):
                return True
    return False
