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
from pymongo.collection import Collection
from bson import ObjectId
from app.models.schemas.comments import ListOfCommentsInResponse

from pymongo.collection import Collection
from bson import ObjectId
from app.models.schemas.comments import ListOfCommentsInResponse, CommentInCreate, CommentInResponse

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
    await comments_repo.delete_comment(comment=comment)


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
    comment_data = {
        "body": comment_create.body,
        "article_id": ObjectId(article.id),
        "user_id": ObjectId(user.id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    comment_id = comments_repo.collection.insert_one(comment_data).inserted_id
    comment_data["_id"] = comment_id

    # Update the article document to include the new comment ID
    comments_repo.collection.update_one(
        {"_id": ObjectId(article.id)},
        {"$push": {"comments": comment_id}}
    )

    comment = Comment(**comment_data)
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
    comments_collection: Collection = comments_repo.collection
    article_id = ObjectId(article.id)
    
    comments_cursor = comments_collection.find({"article_id": article_id})
    comments = await comments_cursor.to_list(length=None)
    
    return ListOfCommentsInResponse(comments=comments)
