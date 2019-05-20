from flask import Flask
from flask_restful import Api, Resource, reqparse
from flask_restful_swagger import swagger

from objects import State, ServoNotFound, MovementOutOfRange,\
    PresetNotFound, PresetMember, PresetMemberPositionOutOfRange

try:
    from servocontrol import PTZServo
except ModuleNotFoundError:
    from fakes.servocontrol import PTZServo

app = Flask(__name__)
api = swagger.docs(Api(app), apiVersion='0.1',
                   basePath='http://localhost:5000',
                   resourcePath='/',
                   produces=["application/json", "text/html"],
                   api_spec_url='/api/spec',
                   description='API to control servos on a Raspberry Pi')

ptzservo = PTZServo()
appstate = State()


class APIError(object):
    error = None
    message = None
    item = None

    def __init__(self, message, item=None, error=None):
        self.message = message
        self.error = error
        self.item = item

    def format(self):
        resp = {"message": self.message}
        if self.item:
            resp["item"] = self.item
        if self.error:
            resp["error"] = self.error.__class__.__name__
        return resp


def error_response_creator(*error: APIError):
    return {"errors": [e.format() for e in error]}


class ServoResource(Resource):
    @staticmethod
    def get(name=None):
        if name:
            try:
                return appstate.servos.get(name).serialize(), 200
            except ServoNotFound as e:
                return error_response_creator(APIError(e.msg, name, e)), 404
        else:
            return appstate.servos.dump(), 200

    @staticmethod
    def put(name):
        parser = reqparse.RequestParser()
        parser.add_argument("limit_min", type=int)
        parser.add_argument("limit_max", type=int)
        parser.add_argument("channel", type=int)
        args = parser.parse_args()

        new_servo = {
            "limits": {
                "min": args["limit_min"],
                "max": args["limit_max"]
            },
            "channel": args["channel"]
        }
        created = appstate.servos.new(name, new_servo)
        appstate.dump()
        return created.serialize(), 201

    @staticmethod
    def delete(name):
        try:
            appstate.servos.delete(name)
            return "Deleted: {}".format(name), 200
        except ServoNotFound as e:
            return error_response_creator(APIError(e.msg, name, e)), 404


class AbsPositionResource(Resource):
    @staticmethod
    def get(name=None):
        if name:
            try:
                return appstate.servos.get(name).position, 200
            except ServoNotFound as e:
                return error_response_creator(APIError(e.msg, name, e)), 404
        else:
            return appstate.servos.positions(), 200

    @staticmethod
    def post(name=None):
        parser = reqparse.RequestParser()
        if name:
            parser.add_argument("position", type=int, required=True)
            args = parser.parse_args()
            try:
                move = appstate.servos.get(name).move_absolute(args["position"]).serialize()
                appstate.dump()
                return move, 200
            except MovementOutOfRange as e:
                return error_response_creator(APIError(e.msg, name, e)), 403
            except ServoNotFound as e:
                return error_response_creator(APIError(e.msg, name, e)), 404
        else:
            parser.add_argument("position", type=dict, required=True, location='json')
            args = parser.parse_args()
            errors = []
            success = []
            for name, position in args["position"].items():
                try:
                    appstate.servos.get(name).move_absolute(position)
                    success.append(name)
                except (MovementOutOfRange, ServoNotFound) as e:
                    errors.append(APIError(e.msg, name, e))
            if errors:
                if len(errors) != len(args["position"]):
                    resp = error_response_creator(*errors)
                    resp["positions"] = [
                                   {"name": position, "position": appstate.servos.get(position).position}
                                   for position in args["position"] if position in success]
                    appstate.dump()
                    return resp, 207
                else:
                    return error_response_creator(*errors), 400
            appstate.dump()
            return {"positions": args["position"]}, 200


class RelPositionResource(Resource):
    @staticmethod
    def post(name):
        parser = reqparse.RequestParser()
        parser.add_argument("movement", type=int, required=True)
        args = parser.parse_args()
        try:
            move = appstate.servos.get(name).move_relative(args["movement"]).serialize()
            appstate.dump()
            return move, 200
        except ServoNotFound as e:
            return error_response_creator(APIError(e.msg, name, e)), 404


class PresetResource(Resource):
    @staticmethod
    def get(name=None):
        if name:
            try:
                return appstate.presets.get(name), 200
            except PresetNotFound as e:
                return error_response_creator(APIError(e.msg, name, e)), 404
        else:
            return appstate.presets.dump(), 200

    @staticmethod
    def post(name):
        try:
            appstate.presets.get(name).apply()
            appstate.dump()
            return "", 204
        except PresetNotFound as e:
            return error_response_creator(APIError(e.msg, name, e)), 404

    @staticmethod
    def put(name):
        parser = reqparse.RequestParser()
        parser.add_argument("servos", type=dict)
        args = parser.parse_args()

        preset_members = []
        for servo, position in args["servos"].items():
            try:
                preset_members.append(PresetMember(appstate.servos.get(servo), position))
            except PresetMemberPositionOutOfRange as e:
                return error_response_creator(APIError(e.msg, servo, e)), 403

        if name in appstate.presets.all().keys():
            appstate.presets.new(name, *preset_members)
            appstate.dump()
            return appstate.presets.get(name).serialize(), 200
        else:
            appstate.presets.new(name, *preset_members)
            appstate.dump()
            return appstate.presets.get(name).serialize(), 201

    @staticmethod
    def delete(name):
        try:
            appstate.presets.delete(name)
            appstate.dump()
            return "Deleted: {}".format(name), 200
        except PresetNotFound as e:
            return error_response_creator(APIError(e.msg, name, e)), 404


api.add_resource(ServoResource, "/servo/<string:name>", "/servos")
api.add_resource(AbsPositionResource, "/absolute/<string:name>", "/absolute")
api.add_resource(RelPositionResource, "/relative/<string:name>")
api.add_resource(PresetResource, "/preset/<string:name>", "/presets")

if __name__ == "__main__":
    app.run(debug=True)
