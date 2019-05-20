import json

try:
    from servocontrol import PTZServo
except ModuleNotFoundError:
    from fakes.servocontrol import PTZServo


class CustomError(Exception):
    """Base Class for custom Exceptions"""
    pass


class OutOfRange(CustomError):
    """Raised when something is outside of the allowed range
    Attributes:
        current -- the current position
        next -- attempted new position
        allowed_range -- The min and max limits
        message -- explanation of why this is not allowed
        """
    def __init__(self, current, desired, allowed_range, message=None):
        self.current = current
        self.desired = desired
        self.allowed_range = allowed_range
        self.msg = message


class MovementOutOfRange(OutOfRange):
    """Raised when a movement is outside of the allowed range of that servo

    Attributes:
        current -- the current position
        next -- attempted new position
        allowed_range -- The min and max limits for this servo
        message -- explanation of why this specific movement is not allowed
        """


class PresetMemberPositionOutOfRange(OutOfRange):
    """Raised when a preset's set movement is outside of the allowed range

    Attributes:
        current -- the current position
        next -- attempted new position
        allowed_range -- The min and max limits for this servo
        message -- explanation of why this specific movement is not allowed
        """
    def __init__(self, desired, allowed_range, message=None):
        self.desired = desired
        self.allowed_range = allowed_range
        self.msg = message


class NotFound(CustomError):
    """Raised when a something does not exist

    Attributes:
        message -- a friendly message describing the error
        """
    def __init__(self):
        self.msg = "not found"


class ServoNotFound(NotFound):
    """Raised when a servo does not exist

    Attributes:
        message -- a friendly message describing the error
        """
    def __init__(self):
        self.msg = "Servo not found"


class PresetNotFound(NotFound):
    """Raised when a preset does not exist

    Attributes:
        message -- a friendly message describing the error
        """
    def __init__(self):
        self.msg = "Preset not found"


class Servo(object):
    limit_min = -1
    limit_max = -1
    channel = -1
    position = -1
    ptzservo = None
    name = None

    def __init__(self, ptzservo, name, limit_min, limit_max, channel, position=None):
        self.name = name
        self.limit_min = limit_min
        self.limit_max = limit_max
        self.channel = channel
        if position:
            self.position = position
        else:
            self.position = limit_min
        self.ptzservo = ptzservo

    def serialize(self) -> dict:
        return {
            "position": self.position,
            "channel": self.channel,
            "limits": {
                "min": self.limit_min,
                "max": self.limit_max
            }
        }

    def update(self, limit_min=None, limit_max=None, channel=None) -> 'Servo':
        if limit_min:
            self.limit_min = limit_min
        if limit_max:
            self.limit_max = limit_max
        if channel:
            self.channel = channel
        return self

    def get_channel(self) -> int:
        return self.channel

    def get_position(self) -> int:
        return self.position

    def make_it_so(self):
        self.ptzservo.set_position(self.channel, self.position)

    def move_absolute(self, position) -> 'Servo':
        if self.limit_min <= position <= self.limit_max:
            self.position = position
            self.make_it_so()
            return self
        else:
            raise MovementOutOfRange(
                self.position,
                position,
                (self.limit_min, self.limit_max),
                "Position {} is {} than {}".format(
                    position,
                    "lower" if position < self.limit_min else "higher",
                    self.limit_min if position < self.limit_min else self.limit_max,
                ))

    def move_relative(self, movement) -> 'Servo':
        desired_position = self.position + movement
        if desired_position < self.limit_min:
            desired_position = self.limit_min
        if desired_position > self.limit_max:
            desired_position = self.limit_max
        self.position = desired_position
        self.make_it_so()

        return self


class Servos(object):
    """Collection of Servo objects

    Attributes:
        servos -- A dict of "name": Servo
        ptzservo -- An instance of PTZServo
    """
    servos = {}
    ptzservo = None

    def __init__(self):
        self.ptzservo = PTZServo()
        pass

    def new(self, name, data) -> Servo:
        self.servos[name] = Servo(
            self.ptzservo,
            name,
            data["limits"]["min"],
            data["limits"]["max"],
            data["channel"],
            data["position"] if "position" in data.keys() else None
        )
        return self.servos[name]

    def delete(self, name) -> None:
        try:
            del self.servos[name]
        except KeyError:
            raise ServoNotFound()

    def populate(self, populate_data):
        for name, data in populate_data.items():
            self.new(name, data)

    def get(self, name) -> Servo:
        try:
            return self.servos[name]
        except KeyError:
            raise ServoNotFound()

    def positions(self) -> dict:
        data = {}
        for name, servo in self.servos.items():
            data[name] = servo.position
        return data

    def all(self) -> dict:
        return self.servos

    def dump(self) -> dict:
        dump_data = {}
        for name, servo in self.servos.items():
            dump_data[name] = servo.serialize()
        return dump_data


class PresetMember(object):
    servo = None
    position = -1

    def __init__(self, servo: Servo, position: int):
        if servo.limit_min <= position <= servo.limit_max:
            self.position = position
            self.servo = servo
        else:
            raise PresetMemberPositionOutOfRange(
                desired=servo.position,
                allowed_range=(servo.limit_min, servo.limit_max),
                message="Position {} is {} than {}".format(
                    position,
                    "lower" if position < servo.limit_min else "higher",
                    servo.limit_min if position < servo.limit_min else servo.limit_max,
                ))

    def serialize(self):
        return {"servo": self.servo.name, "position": self.position}

    def apply(self):
        return self.servo.move_absolute(self.position)


class Preset(object):
    members = []

    def __init__(self, *members: PresetMember):
        for member in members:
            self.members.append(member)

    def serialize(self) -> dict:
        return {member.servo.name: member.position for member in self.members}

    def apply(self):
        for member in self.members:
            member.apply()


class Presets(object):
    """Collection of Preset objects

    Attributes:
        presets -- A dict of "name": preset
    """
    presets = {}
    servos = None

    def __init__(self, servos: Servos):
        self.servos = servos

    def new(self, name: str, *members: PresetMember) -> Preset:
        self.presets[name] = Preset(*members)
        return self.presets[name]

    def delete(self, name) -> None:
        try:
            del self.presets[name]
        except KeyError:
            raise PresetNotFound()

    def populate(self, populate_data: dict):
        for name, data in populate_data.items():
            members = []
            for servo_name, position in data.items():
                members.append(PresetMember(self.servos.get(servo_name), position))
            self.new(name, *members)

    def get(self, name) -> Preset:
        try:
            return self.presets[name]
        except KeyError:
            raise PresetNotFound()

    def all(self) -> dict:
        return self.presets

    def dump(self) -> dict:
        dump_data = {}
        for name, preset in self.presets.items():
            dump_data[name] = preset.serialize()
        return dump_data


class State(object):
    servos = Servos()
    presets = Presets(servos)

    def __init__(self):
        try:
            with open("servos.json", "r") as f:
                self.servos.populate(json.load(f))
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            pass

        try:
            with open("presets.json", "r") as f:
                self.presets.populate(json.load(f))
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            pass

    def dump(self):
        with open("servos.json", "w") as f:
            json.dump(self.servos.dump(), f)

        with open("presets.json", "w") as f:
            json.dump(self.presets.dump(), f)
