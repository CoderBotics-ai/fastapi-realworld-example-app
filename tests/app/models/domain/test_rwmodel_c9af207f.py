import pytest
from unittest.mock import MagicMock
from datetime import datetime
from pydantic import BaseModel, BaseConfig
from app.models.domain.rwmodel import convert_datetime_to_realworld, convert_field_to_camel_case, RWModel



def mock_convert_datetime_to_realworld(dt):
    return '2022-01-01T00:00:00Z'

def mock_convert_field_to_camel_case(string):
    return 'mockedCamelCase'

def test_convert_datetime_to_realworld():
    dt = datetime(2022, 1, 1)
    assert convert_datetime_to_realworld(dt) == '2022-01-01T00:00:00Z'

def test_convert_field_to_camel_case():
    assert convert_field_to_camel_case('hello_world') == 'HelloWorld'

def test_rwmodel_config():
    model = RWModel()
    assert model.Config.allow_population_by_field_name == True
    assert model.Config.json_encoders == {datetime.datetime: convert_datetime_to_realworld}
    assert model.Config.alias_generator == convert_field_to_camel_case

def test_rwmodel_config_with_mocked_functions(mocker):
    mocker.patch('app.models.domain.rwmodel.convert_datetime_to_realworld', side_effect=mock_convert_datetime_to_realworld)
    mocker.patch('app.models.domain.rwmodel.convert_field_to_camel_case', side_effect=mock_convert_field_to_camel_case)
    model = RWModel()
    assert model.Config.json_encoders == {datetime.datetime: mock_convert_datetime_to_realworld}
    assert model.Config.alias_generator == mock_convert_field_to_camel_case