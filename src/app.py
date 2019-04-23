import json
import atexit

from flask import Flask
from flask_restful import Api, Resource, reqparse

from servocontrol import PTZServo

app = Flask(__name__)
api = Api(app)

servos = {}
with open('servos.json', 'r') as f:
    servos = json.load(f)

curpos = {}
with open('curpos.json', 'r') as f:
    curpos = json.load(f)

def write_out_json_files():
    with open('servos.json', 'w') as f:
        json.dump(servos, f)
    with open('curpos.json', 'w') as f:
        json.dump(curpos, f)
atexit.register(write_out_json_files)

ptzservo = PTZServo()

class Servo(Resource):
    def get(self, name=None):
        if name:
            if name in servos.keys():
                return servos[name], 200
            else:
                return "Servo with name {} not found".format(name), 404
        else:
            return servos, 200

    def post(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("limit_min", type=int, required=True)
        parser.add_argument("limit_max", type=int, required=True)
        parser.add_argument("channel", type=int, required=True)
        args = parser.parse_args()
        if name in servos.keys():
            return "Servo with name {} already exists".format(name), 400
        newServo = {
            "limits": {
                "min": args["limit_min"],
                "max": args["limit_max"]
            },
            "channel": args["channel"]
        }
        servos[name] = newServo
        write_out_json_files()
        return newServo, 201


    def put(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("limit_min", type=int)
        parser.add_argument("limit_max", type=int)
        parser.add_argument("channel", type=int)
        args = parser.parse_args()

        if name in servos.keys():
            servos[name] = {
                "limits": {
                    "min": args["limit_min"],
                    "max": args["limit_max"]
                },
                "channel": args["channel"]
            }
            write_out_json_files()
            return servos[name], 200
        newServo = {
            "limits": {
                "min": limit_min,
                "max": limit_max
            },
            "channel": args["channel"]
        }
        servos[name] = newServo
        write_out_json_files()
        return newServo, 201


    def delete(self, name):
        try:
            del servos[name]
            write_out_json_files()
            return "Deleted: {}".format(name), 200
        except KeyError:
            return "User with name {} not found".format(name), 404


class AbsPosition(Resource):
    def get(self, name=None):
        if name:
            if name in servos.keys():
                if name in curpos.keys():
                    return {"position": curpos[name]}, 200
                else:
                    return "Position for servo {} not found".format(name), 404
            else:
                return "Servo with name {} not found".format(name), 404
        else:
            return {"positions": curpos}, 200

    def post(self, name=None):
        parser = reqparse.RequestParser()
        if name:
            parser.add_argument("position", type=int, required=True)
            args = parser.parse_args()
            if name in servos.keys():
                if servos[name]["limits"]["min"] <= args["position"] <= servos[name]["limits"]["max"]:
                    ptzservo.set_position(servos[name]["channel"], args["position"])
                    curpos[name] = args["position"]
                    write_out_json_files()
                    return {"position": curpos[name]}, 200
                else:
                    return "Position {} out of range for servo {}. Valid range: {} to {}".format(args["position"], name, servos[name]["limits"]["min"], servos[name]["limits"]["max"]), 400
            return "Servo {} not found".format(name), 404
        else:
            parser.add_argument("position", type=list, required=True, location='json')
            args = parser.parse_args()
            errors = []
            success = []
            for servo in args["position"]:
                if servos[servo["name"]]["limits"]["min"] <= servo["position"] <= servos[servo["name"]]["limits"]["max"]:
                    ptzservo.set_position(servos[servo["name"]]["channel"], servo["position"])
                    curpos[servo["name"]] = servo["position"]
                    success.append(servo["name"])
                    write_out_json_files()
                else:
                    errors.append("Position {} out of range for servo {}. Valid range: {} to {}".format(servo["position"], servo["name"], servos[servo["name"]]["limits"]["min"], servos[servo["name"]]["limits"]["max"]))
            if errors:
                if len(errors) != len(args["position"]):
                    return {"errors": errors, "positions": [{"name": position["name"], "position": curpos[position["name"]]} for position in args["position"] if position["name"] in success]}, 200
                else:
                    return {"errors": errors}, 400
            return {"positions": args["position"]}, 200



class RelPosition(Resource):
    def post(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("movement", type=int, required=True)
        args = parser.parse_args()
        if name in servos.keys():
            desired_position = curpos[name] + args["movement"]
            if desired_position < servos[name]["limits"]["min"]:
                desired_position = servos[name]["limits"]["min"]
            if desired_position > servos[name]["limits"]["max"]:
                desired_position = servos[name]["limits"]["max"]
            ptzservo.set_position(servos[name]["channel"], desired_position)
            curpos[name] = desired_position
            write_out_json_files()
            return {"position": curpos[name]}, 200
        return "Servo {} not found".format(name), 404

api.add_resource(Servo, "/servo/<string:name>", "/servos")
api.add_resource(AbsPosition, "/absolute/<string:name>", "/absolute")
api.add_resource(RelPosition, "/relative/<string:name>")

if __name__ == "__main__":
    app.run(debug=True)
