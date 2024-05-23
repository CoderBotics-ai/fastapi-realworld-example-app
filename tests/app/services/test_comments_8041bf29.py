import pytest
from unittest.mock import patch
from bson import ObjectId
from app.services.comments import check_user_can_modify_comment
from app.models.domain.comments import Comment
from app.models.domain.users import User



@pytest.fixture
def mock_comment():
    return Comment(created_at=None, updated_at=None, id_='507f1f77bcf86cd799439011', body='Test body', author=None)

@pytest.fixture
def mock_user():
    return User(username='Test author', email='test@example.com', bio='', image=None)

def test_check_user_can_modify_comment_true(mock_comment, mock_user):
    with patch('app.services.comments.users_collection.find_one') as mock_find_one:
        mock_find_one.return_value = {
            'username': 'Test author',
            'comments': [{'comment_id': ObjectId(mock_comment.id_)}]
        }
        result = check_user_can_modify_comment(mock_comment, mock_user)
        assert result is True

def test_check_user_can_modify_comment_false(mock_comment, mock_user):
    with patch('app.services.comments.users_collection.find_one') as mock_find_one:
        mock_find_one.return_value = {
            'username': 'Test author',
            'comments': [{'comment_id': ObjectId()}]
        }
        result = check_user_can_modify_comment(mock_comment, mock_user)
        assert result is False

def test_check_user_can_modify_comment_no_user_data(mock_comment, mock_user):
    with patch('app.services.comments.users_collection.find_one') as mock_find_one:
        mock_find_one.return_value = None
        result = check_user_can_modify_comment(mock_comment, mock_user)
        assert result is False