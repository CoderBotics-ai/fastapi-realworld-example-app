import pytest
from app.db.queries.tables import Parameter, TypedTable, Users, Articles, Tags, ArticlesToTags, Favorites

users = Users()
articles = Articles()
tags = Tags()
articles_to_tags = ArticlesToTags()
favorites = Favorites()



def test_parameter_init():
    param = Parameter(1)
    assert param.get_sql() == '$1'

def test_typed_table_init_with_name():
    table = TypedTable(name='test_table')
    assert table._table_name == 'test_table'

def test_typed_table_init_without_name():
    class TestTable(TypedTable):
        __table__ = 'test_table'
    table = TestTable()
    assert table._table_name == 'test_table'

def test_users_table():
    assert users._table_name == 'users'

def test_articles_table():
    assert articles._table_name == 'articles'

def test_tags_table():
    assert tags._table_name == 'tags'

def test_articles_to_tags_table():
    assert articles_to_tags._table_name == 'articles_to_tags'

def test_favorites_table():
    assert favorites._table_name == 'favorites'