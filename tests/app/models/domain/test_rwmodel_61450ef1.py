import pytest
from unittest.mock import MagicMock
from datetime import datetime
from pydantic import BaseModel, BaseConfig
from app.models.domain.rwmodel import convert_datetime_to_realworld, convert_field_to_camel_case, RWModel



def setup_rwmodel():
    return RWModel()

def test_convert_datetime_to_realworld():
    dt = datetime(2022, 1, 1, 12, 0, 0)
    assert convert_datetime_to_realworld(dt) == '2022-01-01T12:00:00Z'

def test_convert_field_to_camel_case():
    assert convert_field_to_camel_case('hello_world') == 'helloWorld'
    assert convert_field_to_camel_case('hello') == 'hello'

def test_rwmodel_config():
    rwmodel = setup_rwmodel()
    assert rwmodel.Config.allow_population_by_field_name == True
    assert rwmodel.Config.json_encoders == {datetime.datetime: convert_datetime_to_realworld}
    assert rwmodel.Config.alias_generator == convert_field_to_camel_case