from unittest import TestCase
from unittest.mock import patch

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool


class TestOriginDestinationVariate(TestCase):
    def setUp(self) -> None:
        test_app = Flask('test_app')
        test_app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        test_app.config['JSON_SORT_KEYS'] = True
        engine = create_engine("postgresql+psycopg2://postgres:ratestask@localhost:5432/postgres")
        connection = engine.connect()

    def test_both_origin_destination_are_port_codes(self):
        with patch(
            "connection.execute()",
            return_value=[]
        ):
            pass

    def test_both_origin_destination_are_regions(self):
        pass

    def test_origin_port_code_and_destination_region(self):
        pass

    def test_origin_region_and_destination_port_code(self):
        pass
