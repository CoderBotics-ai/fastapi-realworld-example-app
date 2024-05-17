from app.api.routes.comments import delete_comment_from_article, create_comment_for_article, list_comments_for_article
from unittest.mock import AsyncMock, MagicMock
from fastapi import Response
from app.models.domain.comments import Comment
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.models.schemas.comments import ListOfCommentsInResponse, CommentInCreate, CommentInResponse
from pymongo.collection import Collection

comments_repo_mock = MagicMock(spec=CommentsRepository)
article_mock = MagicMock(spec=Article)
user_mock = MagicMock(spec=User)
comment_mock = MagicMock(spec=Comment)
collection_mock = MagicMock(spec=Collection)

async def get_comment_by_id_from_path_mock():
    return comment_mock
async def get_article_by_slug_from_path_mock():
    return article_mock
async def get_current_user_authorizer_mock():
    return user_mock
async def get_repository_mock():
    return comments_repo_mock

def test_delete_comment_from_article():
    delete_comment_from_article_mock = AsyncMock(return_value=None)
    comment_mock.id = 'some_id'
    comments_repo_mock.delete_comment = delete_comment_from_article_mock
    response = delete_comment_from_article(comment_mock, comments_repo_mock)
    assert response is None
    delete_comment_from_article_mock.assert_awaited_once_with(comment_mock)

def test_create_comment_for_article():
    create_comment_mock = AsyncMock(return_value=CommentInResponse(comment=comment_mock))
    comment_create_mock = CommentInCreate(body='some_body')
    article_mock.id = 'some_id'
    user_mock.id = 'some_id'
    comments_repo_mock.collection.insert_one = AsyncMock(return_value={'inserted_id': 'some_id'})
    comments_repo_mock.collection.update_one = AsyncMock(return_value=None)
    response = create_comment_for_article(comment_create_mock, article_mock, user_mock, comments_repo_mock)
    assert isinstance(response, CommentInResponse)
    create_comment_mock.assert_awaited_once_with(comment_create_mock, article_mock, user_mock, comments_repo_mock)

def test_list_comments_for_article():
    list_comments_mock = AsyncMock(return_value=ListOfCommentsInResponse(comments=[comment_mock]))
    article_mock.id = 'some_id'
    comments_repo_mock.collection.find = AsyncMock(return_value=[comment_mock])
    response = list_comments_for_article(article_mock, user_mock, comments_repo_mock)
    assert isinstance(response, ListOfCommentsInResponse)
    list_comments_mock.assert_awaited_once_with(article_mock, user_mock, comments_repo_mock)