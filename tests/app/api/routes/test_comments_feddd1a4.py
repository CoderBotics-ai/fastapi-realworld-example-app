import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.api.routes.comments import delete_comment_from_article, create_comment_for_article, list_comments_for_article
from app.models.domain.comments import Comment
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.models.schemas.comments import CommentInCreate, CommentInResponse, ListOfCommentsInResponse
from app.db.repositories.comments import CommentsRepository
from bson import ObjectId
from datetime import datetime

@pytest.fixture
def mock_comment():
    return Comment(id=ObjectId(), body='Test comment', article_id=ObjectId(), user_id=ObjectId(), created_at=datetime.utcnow(), updated_at=datetime.utcnow())

@pytest.fixture
def mock_article():
    return Article(id=ObjectId(), slug='test-article')

@pytest.fixture
def mock_user():
    return User(id=ObjectId(), username='testuser')

@pytest.fixture
def mock_comments_repo():
    repo = MagicMock(spec=CommentsRepository)
    return repo

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)



def test_delete_comment_from_article(client, mock_comment, mock_comments_repo):
    with patch('app.api.routes.comments.MongoClient') as MockMongoClient:
        mock_db = MockMongoClient.return_value['your_database_name']
        mock_comments_collection = mock_db['comments']
        mock_articles_collection = mock_db['articles']

        mock_comments_collection.delete_one.return_value = None
        mock_articles_collection.update_one.return_value = None

        response = client.delete(f'/comments/{mock_comment.id}')

        assert response.status_code == 204
        mock_comments_collection.delete_one.assert_called_once_with({'_id': ObjectId(mock_comment.id)})
        mock_articles_collection.update_one.assert_called_once_with({'_id': ObjectId(mock_comment.article_id)}, {'$pull': {'comments': ObjectId(mock_comment.id)}})

def test_create_comment_for_article(client, mock_comment, mock_article, mock_user, mock_comments_repo):
    comment_create = CommentInCreate(body='Test comment body')

    with patch('app.api.routes.comments.MongoClient') as MockMongoClient:
        mock_db = MockMongoClient.return_value['your_database_name']
        mock_comments_collection = mock_db['comments']
        mock_articles_collection = mock_db['articles']

        mock_comments_collection.insert_one.return_value.inserted_id = ObjectId()
        mock_articles_collection.update_one.return_value = None

        response = client.post('/comments', json={'comment': comment_create.dict()})

        assert response.status_code == 201
        assert response.json()['comment']['body'] == 'Test comment body'
        mock_comments_collection.insert_one.assert_called_once()
        mock_articles_collection.update_one.assert_called_once()

def test_list_comments_for_article(client, mock_article, mock_user, mock_comments_repo):
    mock_comments_repo.get_comments_for_article.return_value = [mock_comment()]

    response = client.get('/comments')

    assert response.status_code == 200
    assert len(response.json()['comments']) == 1
    assert response.json()['comments'][0]['body'] == 'Test comment'
    mock_comments_repo.get_comments_for_article.assert_called_once_with(article=mock_article, user=mock_user)