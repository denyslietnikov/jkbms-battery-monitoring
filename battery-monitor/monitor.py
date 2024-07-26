import os
import subprocess
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TimedOut
import pytz

# Enable logging
logging.basicConfig(
    format="%(asctime)s;%(name)s;%(levelname)s;%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Read environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEVICE_MAC = os.getenv("DEVICE_MAC")
DEVICE_NAME = os.getenv("DEVICE_NAME")
DEVICE_PROTOCOL = os.getenv("DEVICE_PROTOCOL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", 10))
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/logs/stat.log")
TIMEZONE = os.getenv("TIMEZONE", "UTC")
MIN_VOLTAGE = float(os.getenv("MIN_VOLTAGE", 20))
MAX_VOLTAGE = float(os.getenv("MAX_VOLTAGE", 25))

# Set timezone
tz = pytz.timezone(TIMEZONE)

# Custom time converter for logger
def custom_time(*args):
    utc_dt = datetime.now(tz=pytz.UTC)
    local_dt = utc_dt.astimezone(tz)
    return local_dt.timetuple()

# Adjust logger's time converter
logging.Formatter.converter = custom_time

# Adjust httpx logging level based on LOG_HTTP_REQUESTS
LOG_HTTP_REQUESTS = os.getenv("LOG_HTTP_REQUESTS", "True").lower() in ("true", "1", "yes")
httpx_logger = logging.getLogger("httpx")
if not LOG_HTTP_REQUESTS:
    httpx_logger.setLevel(logging.WARNING)

# Path to the jkbms executable
JKBMS_PATH = "/app/jkbms-monitoring/bin/jkbms"

last_voltage_sent = None
start_time = datetime.now(tz)
chat_id = None
monitoring_started = False

logger.info("Application started")
logger.info(f"Current time: {start_time}")
logger.info("Waiting for /start command")

def reset_log_file_if_new_day():
    now = datetime.now(tz)
    log_file_name = LOG_FILE_PATH
    log_dir = os.path.dirname(log_file_name)
    if os.path.exists(log_file_name):
        last_mod_time = datetime.fromtimestamp(os.path.getmtime(log_file_name), tz)
        if last_mod_time.date() < now.date():
            yesterday = now - timedelta(days=1)
            archive_log_file_name = os.path.join(log_dir, f"stat.{yesterday.strftime('%d-%m-%Y')}.log")
            with open(log_file_name, 'r') as log_file:
                data = log_file.read()
            with open(archive_log_file_name, 'w') as archive_log:
                archive_log.write(data)
            logger.info(f"Archived log file to {archive_log_file_name}")
            with open(log_file_name, 'w') as log_file:
                if chat_id:
                    log_file.write(f"{datetime.now(tz).isoformat()};Chat ID: {chat_id}\n")
            logger.info(f"Created new log file {log_file_name} with Chat ID")

def write_log(message):
    reset_log_file_if_new_day()
    with open(LOG_FILE_PATH, 'a') as log_file:
        log_file.write(f"{datetime.now(tz).isoformat()};{message}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global chat_id, monitoring_started
    # Ignore messages sent before the application started
    if update.message.date < start_time:
        return
    
    chat_id = update.message.chat_id
    logger.info("Received /start command")
    logger.info(f"Chat ID: {chat_id}")
    write_log(f"Chat ID: {chat_id}")
    monitoring_started = True
    await update.message.reply_text("Battery monitoring started.")
    logger.info("Sent: Battery monitoring started.")
    await initial_battery_update(context)
    context.job_queue.run_repeating(send_battery_update, interval=CHECK_INTERVAL, first=CHECK_INTERVAL)

async def initial_battery_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_voltage_sent
    voltage = await get_battery_voltage()
    if voltage is not None:
        try:
            battery_level = (voltage - MIN_VOLTAGE) / (MAX_VOLTAGE - MIN_VOLTAGE) * 100
            await context.bot.send_message(chat_id=chat_id, text=f"Voltage: {voltage:.3f} V, Battery Level: {battery_level:.1f}%")
            logger.info(f"Sent initial voltage: Voltage: {voltage:.3f} V, Battery Level: {battery_level:.1f}%")
            last_voltage_sent = battery_level
            write_log(f"Voltage: {voltage:.3f} V, Battery Level: {battery_level:.1f}%")
        except TimedOut as e:
            logger.error(f"Error sending message: {e}")

async def send_battery_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_voltage_sent
    voltage = await get_battery_voltage()
    if voltage is not None:
        battery_level = (voltage - MIN_VOLTAGE) / (MAX_VOLTAGE - MIN_VOLTAGE) * 100
        write_log(f"Voltage: {voltage:.3f} V, Battery Level: {battery_level:.1f}%")  # Write to stat.log
        if last_voltage_sent is None or abs(battery_level - last_voltage_sent) >= 5:
            change_indicator = ""
            if last_voltage_sent is not None:
                if battery_level > last_voltage_sent:
                    change_indicator = "⬆️"
                elif battery_level < last_voltage_sent:
                    change_indicator = "⬇️"
            await send_message(context, f"Voltage: {voltage:.3f} V, Battery Level: {battery_level:.1f}% {change_indicator}")
            logger.info(f"Sent voltage update: Voltage: {voltage:.3f} V, Battery Level: {battery_level:.1f}% {change_indicator}")
            last_voltage_sent = battery_level
        else:
            logger.info(f"Checked voltage: {voltage:.3f} V, Battery Level: {battery_level:.1f}%")
            logger.info("Voltage change did not meet thresholds for sending update")

async def get_battery_voltage() -> float:
    command = f"{JKBMS_PATH} -p {DEVICE_MAC} -n \"{DEVICE_NAME}\" -P {DEVICE_PROTOCOL} -c getCellData | grep \"voltage\" | awk '{{sum += $2}} END {{print sum}}'"
    logger.info(f"Executing command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Command failed with return code {result.returncode}: {result.stderr}")
        return None
    try:
        voltage = float(result.stdout.strip())
        logger.info(f"Command output: {voltage}")
        return voltage
    except ValueError as e:
        logger.error(f"Error converting command output to float: {e}. Command output: '{result.stdout.strip()}'")
        return None

async def send_message(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    try:
        await context.bot.send_message(chat_id=chat_id, text=text)
    except TimedOut as e:
        logger.error(f"Error sending message: {e}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    logger.info("Connecting to Telegram chat")
    application.run_polling(poll_interval=POLLING_INTERVAL)

if __name__ == "__main__":
    main()