HISTORY_LENGTH = 5
HISTORY_TIMEOUT = 600
INITIAL_MESSAGE = "you are a helpful printer, prioritize: formatting, syntax, and appeal"
MAX_TOKENS = 200
TIMEOUT = 60
DEBUG_ENABLE = True


PRINTER_DEVICE_NAME = "printer"
DEFAULT_PRINTER_IP_ADDRESS = "192.168.1.152"
DEFAULT_PRINTER_IP_PORT = 8888
RETRIES_MAX = 5
PRINTER_CONFIGURATION = {"speed": 8, "line_length": 42, "autocut": 1}
BOT_COMPLETION_TOPIC = "robot/requestCompletion"
BOT_CONTEXT_TOPIC = "robot/addContext"
BOT_RESET_TOPIC = "robot/resetConversation"
BOT_STATUS_TOPIC = "robot/botStatus"
BOT_URL_IMAGE_TOPIC = "robot/webImage"
MAX_TOKENS_TOPIC = "robot/setMaxTokens"
FORMAT_AND_PRINT_TOPIC = "robot/formatAndPrint"
CONFIG_TOPIC = "printer/config"
PRINT_TOPIC = "printer/printText"
CUT_TOPIC = "printer/cut"
FEED_TOPIC = "printer/feed"
IMAGE_TOPIC = "printer/image"
STATUS_TOPIC = "printer/status"
DISCOVER_TOPIC = "esphome/discover" + "/" + PRINTER_DEVICE_NAME
DEVICE_STATUS_TOPIC = "printer/deviceStatus"
DEVICE_ADDRESS_TOPIC = "printer/ipAddress"
STATUS_OPTIONS = ["ready", "generating", "printing", "faulted"]
SUBSCRIBE_TOPICS = [
    BOT_COMPLETION_TOPIC,
    BOT_STATUS_TOPIC,
    BOT_CONTEXT_TOPIC,
    BOT_RESET_TOPIC,
    BOT_URL_IMAGE_TOPIC,
    FORMAT_AND_PRINT_TOPIC,
    DEVICE_STATUS_TOPIC,
    DEVICE_ADDRESS_TOPIC,
    DISCOVER_TOPIC,
    MAX_TOKENS_TOPIC,
]
