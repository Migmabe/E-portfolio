import math


class BoardComputer:

    def __init__(self, destination=(40, 20), status="off", network_antenna_object=None):
        if network_antenna_object is None:
            self.networkantenna = NetworkAntenna()
        self.mileage = Battery().mileage()
        self.status = status
        self.rate = 0.1
        self.brake = True
        self.__manufacturer = "Mike Studios"
        self.__serialno = 1234567
        self._software = 1.0
        self.destination = destination

    def __add__(self, choice):
        """adds and sets if the system is ON or OFF"""
        if choice == "off":
            self.status = "off"
        elif choice == "on":
            self.status = "on"
        elif choice == "q":
            self.status = "q"
        else:
            raise ValueError("System can only be ON or OFF")

    def mutation(self, input_data, process_unit):  # this one will update the object without the external loop, where input_data is the full list
        for n in input_data:
            print(f"{input_data.index(n)}")
            if process_unit.run_mode(n, self) == "Exit":
                return "Exit"

    @property
    def software(self):
        return self._software

    @software.setter
    def software(self, new):
        self._software = new

    def ov_check(self, latest_OV):
        if self.software < latest_OV:
            self.software = latest_OV
            print(f"Software updated to version {self.software}")

    def run_mode(self, input_data, latest_OV, light_threshold):
        while True:
            self + input("Do you want to start the system?: Please enter ON, OFF or (Q)uit\n").lower()
            if self.status == "off":
                print("System OFF")
                break
            elif self.status == "on":
                print("System ON")
                self.ov_check(latest_OV)
                console = ProcessUnit(IMU(), GNSS(), LightSensor(light_threshold), ObstacleDetection())
                while True:
                    try:
                        self.destination = [float(num) for num in
                                            input("""Please enter a destination "x, y":""").split(", ")]
                        break
                    except ValueError:
                        print("Please enter numerical coordinates.")
                if self.mutation(input_data, console) == "Exit":
                    break
            elif self.status == "q":
                print("System Quit by user.")
                break
            else:
                print("Please enter a valid status.")


class NetworkAntenna:
    rate = 0.1

    def __init__(self):
        self.status = "on"


class Battery:

    def __init__(self, discharge=10000):
        self.capacity = 30000
        self.discharge_rate = discharge  # per hour

    def mileage(self):
        """at an assumed average speed of 60 kmh || not in real time"""
        time = self.capacity / self.discharge_rate
        mileage = time * 60
        return mileage


######################################################################################
######################################################################################
######################################################################################
######################################################################################


class ProcessUnit(BoardComputer):

    def __init__(self, imu_object, gnss_object, light_sensor_object, obstacle_detection_object, speed=0):
        super().__init__()
        self.error_list = []
        self.error_count = 0
        self.speed = speed
        self.imu = imu_object
        self.gnss = gnss_object
        self.lightsensor = light_sensor_object
        self.obstacle_detection = obstacle_detection_object
        self.process_data = {
            "Speed": 0,
            "Location": [0, 0],
            "Lights": bool(0)
        }

    def updater(self, upper_object):
        """where car1 is my car object or hardware control object"""
        upper_object.error_count = len(self.errors)
        upper_object.error_count = self.errors

    def accelerate(self, input_data):
        """where acceleration comes from IMU and times from CSV - mainly used in"""
        if self.brake is False:
            self.speed = self.speed + self.imu.get_acceleration(input_data) * self.rate
            self.process_data["Speed"] = self.speed
            print(f"Speed is now: {self.speed}")
        elif self.brake is True:
            self.speed = self.speed - self.imu.get_acceleration(input_data) * self.rate
            self.process_data["Speed"] = self.speed
            print(f"Speed is now: {self.speed}")

    def brake_func(self, location, n):
        """where input is location list[] from imu"""
        print(f"Vehicle braking. Position {location}")
        self.accelerate(n)
        if self.speed <= 0:
            self.speed = 0
            print(f"Vehicle halted at {location}")

    def choice(self, n):
        self.obstacle_detection.get_obstacle(n)
        if self.obstacle_detection.obstacle is True:
            self.brake = True
        elif self.obstacle_detection.obstacle is False:
            self.brake = False

    def run_mode(self, n, car1):
        self.lights()
        HardwareControl(self).updater(self)
        if all(abs(x) >= abs(y) for x, y in zip(self.process_data["Location"], car1.destination)):
            print("You have arrived!")
            car1.status = "off"
            return "Exit"
        else:
            self.choice(n)
            if self.brake is False:
                self.accelerate(n)  # assumed time interval of 0.01 --> feedback rate from sensors 100Hz
                pos = self.location(n)
                print(f"Moving... position coordinates {pos}")
            elif self.brake is True:
                pos = self.location(n)
                self.brake_func(pos, n)

    def location(self, n):
        """do average between get_position and get_location"""
        if self.imu.position is not None and self.gnss.location is not None:
            self.process_data["Location"] = self.imu.new_position(n, self)
            return self.imu.position

    def lights(self):
        if self.lightsensor.threshold > 3:
            self.process_data["Lights"] = bool(1)
            print("Lights ON")
        else:
            self.process_data["Lights"] = bool(0)
            print("Lights OFF")


class GNSS:

    def __init__(self, latitude=0, longitude=0):
        self._latitude = latitude
        self._longitude = longitude
        self.speed = 0

    @property
    def location(self):
        return [self._latitude, self._longitude]

    @location.setter
    def location(self, new_value):
        """where new_value is basically input data n[3] and n[4]"""
        self.location = [new_value[3], new_value[4]]


class ObstacleDetection:

    def __init__(self, range_=50):
        """where range is in metres"""
        self.__range = range_
        self.obstacle = False

    def get_obstacle(self, n):
        if n[5] == "True":
            self.obstacle = True
        else:
            self.obstacle = False


class IMU:
    """With acceleration over time and orientation, it can get its position in coordinates"""

    rate = 0.1  # in this case corresponds to the one from the OnBoardComputer but it may not as it is an individual

    # component on its own

    def __init__(self, acceleration=0):
        self.acceleration = acceleration
        self._orientation = 0
        self._position = [0, 0]

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, new_value):
        """where the orientation must be the 3rd column value or input_data[2]"""
        try:
            self._orientation = float(new_value[2])
        except:
            self.cardinal_directions(new_value[2])

    @property
    def position(self):
        return self._position

    def cardinal_directions(self, direction):
        """where direction == new_value from orientation function"""
        if direction.lower() == "north":
            self._orientation = 90
        elif direction.lower() == "south":
            self._orientation = 270
        elif direction.lower() == "east":
            self._orientation = 0
        elif direction.lower() == "west":
            self._orientation = 180
        else:
            raise ValueError("Invalid orientation")

    def get_acceleration(self, input_data):
        """where new_value must be the 2nd column of the row being called in input_data[1]"""
        self.acceleration = float(input_data[1])
        return self.acceleration

    def new_position(self, input_data, computer):
        self.orientation = input_data
        self.position[0] = self.position[0] + math.cos(2 * math.pi * self.orientation / 360)*(computer.speed * float(input_data[0]) + self.get_acceleration(input_data) * float(input_data[0]))
        self.position[1] = self.position[1] + math.sin(2 * math.pi * self.orientation / 360)*(computer.speed * float(input_data[0]) + self.get_acceleration(input_data) * float(input_data[0]))
        return self.position


class LightSensor:
    """Sets the light sensor, absolute darkness being 0"""

    def __init__(self, threshold=0):
        self._threshold = threshold

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, new_value):
        if type(new_value) is int:
            self._threshold = new_value
        else:
            raise ValueError("Light Threshold must be numerical")


######################################################################################
######################################################################################
######################################################################################
######################################################################################


class HardwareControl(ProcessUnit):

    def __init__(self, process_unit):
        self.process_unit = process_unit
        self.hardware = ElectricalMotor(self.process_unit.speed, self.process_unit.brake)
        self.errors = self.hardware.errors

    def error(self):
        self.process_unit.error_list.append(self.errors)
        self.process_unit.error_count = len(self.errors)

    """Here we use the updater function inherited from the class to retrofeed the data to the computer"""


class Light:

    def __init__(self, brightness, blink_rate, colour):
        self.brightness = brightness
        self.blink_rate = blink_rate
        self.colour = colour

    def error(self, hardware):
        if type(self.colour) is not str:
            hardware.errors.append("Colour must be a string")
        if type(self.brightness) is str:
            hardware.errors.append("Brightness must be a number")
        if type(self.colour) is str:
            hardware.errors.append("Blink rate must be a number")


class ElectricalMotor:

    def __init__(self, linear_vel, status):
        self.linear_vel = linear_vel
        self.wheel = Wheel(status)
        self.errors = self.wheel.errors
        self.angular_velocity = 2 * self.linear_vel / self.wheel.size  # 2 added as the wheel size is the diameter not radius

    def error(self):
        if self.linear_vel < 0:
            self.errors.append("Linear velocity reverted in electrical motor level")
        return self.errors


class Wheel:

    def __init__(self, status):
        self.size = 17
        self.brake = Brake(status)  # returns a list of errors and creates light objects
        self.errors = self.brake.errors

    def error(self):
        if self.size > 18:
            self.errors.append("Wheel size bigger than 18")
        if type(self.size) is str:
            self.errors.append("Wheel size invalid")
        return self.brake


class Brake:

    def __init__(self, status):
        self.errors = []
        if status == "True":
            self.light_on()
        else:
            self.light_off()

    def light_on(self):
        return Light(100, 0, "red").error(self)

    def light_off(self):
        return Light(0, 0, "red").error(self)

    def error(self, status):
        if type(status) is not bool:
            self.errors.append("Braking status invalid")
            return self.errors
