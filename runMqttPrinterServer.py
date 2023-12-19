import mqttPrinter
import robot

robot = robot.Robot()
printer = mqttPrinter.MqttPrinter(daemon=True, inRobot=robot)
