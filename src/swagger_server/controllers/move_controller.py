import connexion
import six

from swagger_server.models.abs_position import AbsPosition  # noqa: E501
from swagger_server.models.rel_position import RelPosition  # noqa: E501
from swagger_server import util


def move_abs(body):  # noqa: E501
    """Move the camera to point in an absolute direction

     # noqa: E501

    :param body: Object describing new position of camera
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = AbsPosition.from_dict(connexion.request.get_json())  # noqa: E501
    return body


def move_relative(body):  # noqa: E501
    """Move the camera relative to its current position

     # noqa: E501

    :param body: Object describing new position of camera
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = RelPosition.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
