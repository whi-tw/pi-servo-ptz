# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.abs_position import AbsPosition  # noqa: E501
from swagger_server.models.rel_position import RelPosition  # noqa: E501
from swagger_server.test import BaseTestCase


class TestMoveController(BaseTestCase):
    """MoveController integration test stubs"""

    def test_move_abs(self):
        """Test case for move_abs

        Move the camera to point in an absolute direction
        """
        body = AbsPosition()
        response = self.client.open(
            '/v2/absolute',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_move_relative(self):
        """Test case for move_relative

        Move the camera relative to its current position
        """
        body = RelPosition()
        response = self.client.open(
            '/v2/relative',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
