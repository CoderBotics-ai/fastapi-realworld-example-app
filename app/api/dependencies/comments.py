from typing import Optional

from fastapi import Depends, HTTPException, Path
from starlette import status

from app.api.dependencies import articles, authentication, database
from app.db.errors import EntityDoesNotExist
from app.db.repositories.comments import CommentsRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from app.resources import strings
from app.services.comments import check_user_can_modify_comment
from bson import ObjectId
from pymongo.collection import Collection


async def get_comment_by_id_from_path(
    comment_id: int = Path(..., ge=1),
    article: Article = Depends(articles.get_article_by_slug_from_path),
    user: Optional[User] = Depends(
        authentication.get_current_user_authorizer(required=False),
    ),
    comments_repo: Collection = Depends(
        database.get_collection("users"),  # Assuming comments are embedded in users collection
    ),
) -> Comment:
    try:
        comment_data = comments_repo.find_one(
            {"comments.comment_id": ObjectId(comment_id)},
            {"comments.$": 1}
        )
        if not comment_data or "comments" not in comment_data or len(comment_data["comments"]) == 0:
            raise EntityDoesNotExist()

        comment_info = comment_data["comments"][0]
        return Comment(
            id=str(comment_info["comment_id"]),
            body=comment_info["body"],
            article_id=str(comment_info["article_id"]),
            created_at=comment_info["created_at"],
            updated_at=comment_info["updated_at"]
        )
    except EntityDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=strings.COMMENT_DOES_NOT_EXIST,
        )


def check_comment_modification_permissions(
    comment: Comment = Depends(get_comment_by_id_from_path),
    user: User = Depends(authentication.get_current_user_authorizer()),
) -> None:
    if not check_user_can_modify_comment(comment, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=strings.USER_IS_NOT_AUTHOR_OF_ARTICLE,
        )
