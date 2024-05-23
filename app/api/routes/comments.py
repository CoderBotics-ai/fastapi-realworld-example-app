from typing import Optional

from fastapi import APIRouter, Body, Depends, Response
from starlette import status

from app.api.dependencies.articles import get_article_by_slug_from_path
from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.db.repositories.comments import CommentsRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from typing import Optional, List
from fastapi import APIRouter, Depends
from app.models.schemas.comments import ListOfCommentsInResponse
from pymongo.collection import Collection
from pymongo import MongoClient
from bson import ObjectId

from pymongo import MongoClient
from typing import List

from datetime import datetime


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="comments:delete-comment-from-article",
    dependencies=[Depends(check_comment_modification_permissions)],
    response_class=Response,
)
async def delete_comment_from_article(
    comment: Comment = Depends(get_comment_by_id_from_path),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    articles_collection: Collection = db["articles"]
    comments_collection: Collection = db["comments"]

    # Delete the comment from the comments collection
    comments_collection.delete_one({"_id": ObjectId(comment.comment_id)})

    # Remove the comment reference from the article's comments array
    articles_collection.update_one(
        {"_id": ObjectId(comment.article_id)},
        {"$pull": {"comments": ObjectId(comment.comment_id)}}
    )

    client.close()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentInResponse,
    name="comments:create-comment-for-article",
)
async def create_comment_for_article(
    comment_create: CommentInCreate = Body(..., embed=True, alias="comment"),
    article: Article = Depends(get_article_by_slug_from_path),
    user: User = Depends(get_current_user_authorizer()),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> CommentInResponse:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    comments_collection: Collection = db["comments"]
    articles_collection: Collection = db["articles"]

    comment_data = {
        "body": comment_create.body,
        "article_id": ObjectId(article.id),
        "user_id": ObjectId(user.id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = comments_collection.insert_one(comment_data)
    comment_id = result.inserted_id

    articles_collection.update_one(
        {"_id": ObjectId(article.id)},
        {"$push": {"comments": comment_id}}
    )

    comment = Comment(
        id=comment_id,
        body=comment_create.body,
        article_id=article.id,
        user_id=user.id,
        created_at=comment_data["created_at"],
        updated_at=comment_data["updated_at"],
    )

    return CommentInResponse(comment=comment)
from app.api.dependencies.comments import (
    check_comment_modification_permissions,
    get_comment_by_id_from_path,
)
from app.models.schemas.comments import (
    CommentInCreate,
    CommentInResponse,
    ListOfCommentsInResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=ListOfCommentsInResponse,
    name="comments:get-comments-for-article",
)
async def list_comments_for_article(
    article: Article = Depends(get_article_by_slug_from_path),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> ListOfCommentsInResponse:
    comments = await comments_repo.get_comments_for_article(article=article, user=user)
    return ListOfCommentsInResponse(comments=comments)
