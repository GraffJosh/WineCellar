HISTORY_LENGTH = 5
HISTORY_TIMEOUT = 600
INITIAL_MESSAGE = "you are a helpful printer, prioritize: formatting, syntax, and appeal"
MAX_TOKENS = 200
TIMEOUT = 60

PRINTER_DEVICE_NAME = "printer"
DEFAULT_PRINTER_IP_ADDRESS = "192.168.1.152"
DEFAULT_PRINTER_IP_PORT = 8888
RETRIES_MAX = 5
PRINTER_CONFIGURATION = {"speed": 8, "line_length": 42, "autocut": 1}
CONFIG_TOPIC = "printer/config"
PRINT_TOPIC = "printer/printText"
CUT_TOPIC = "printer/cut"
FEED_TOPIC = "printer/feed"
IMAGE_TOPIC = "printer/image"
STATUS_TOPIC = "printer/status"
DISCOVER_TOPIC = "esphome/discover" + "/" + PRINTER_DEVICE_NAME
COMPLETION_TOPIC = "printer/requestCompletion"
DEVICE_STATUS_TOPIC = "printer/deviceStatus"
DEVICE_ADDRESS_TOPIC = "printer/ipAddress"
BOT_STATUS_TOPIC = "printer/botStatus"
MAX_TOKENS_TOPIC = "printer/setMaxTokens"
STATUS_OPTIONS = ["ready", "generating", "printing", "faulted"]
SUBSCRIBE_TOPICS = [
    COMPLETION_TOPIC,
    BOT_STATUS_TOPIC,
    DEVICE_STATUS_TOPIC,
    DEVICE_ADDRESS_TOPIC,
    DISCOVER_TOPIC,
    MAX_TOKENS_TOPIC,
]
