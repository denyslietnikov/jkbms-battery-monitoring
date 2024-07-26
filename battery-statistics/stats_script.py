import os
import openai
import logging
import requests
from datetime import datetime, time
from time import sleep
import pytz

# Read environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATA_LOG_FILE = os.getenv("DATA_LOG_FILE")
SUMMARY_TIME = os.getenv("SUMMARY_TIME", "00:00")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_PROMPT = os.getenv("OPENAI_PROMPT", "Summarize the following battery data log:")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# Set timezone
tz = pytz.timezone(TIMEZONE)

def custom_time(*args):
    """Custom time function for logging with timezone."""
    utc_dt = datetime.now(tz=pytz.UTC)
    my_tz = utc_dt.astimezone(tz)
    return my_tz.timetuple()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S %Z%z'
)
logging.Formatter.converter = custom_time
logger = logging.getLogger(__name__)

openai.api_key = OPENAI_API_KEY

def read_log_file():
    """Read the log file and return its content."""
    try:
        with open(DATA_LOG_FILE, "r") as file:
            log_data = file.read()
        logger.info("Successfully read the log file.")
        return log_data
    except Exception as e:
        logger.error(f"Error reading the log file: {e}")
        return None

def send_summary_to_openai(log_data):
    """Send the log data to OpenAI and get a summary."""
    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{OPENAI_PROMPT}\n{log_data}"}
            ]
        )
        summary = response.choices[0].message['content'].strip()
        logger.info("Successfully received summary from OpenAI.")
        return summary
    except Exception as e:
        logger.error(f"Error communicating with OpenAI: {e}")
        return None

def send_message_to_telegram(chat_id, message):
    """Send a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info("Successfully sent message to Telegram.")
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {e}")

def get_chat_id(log_data):
    """Extract the chat ID from the log file content."""
    if log_data:
        for line in log_data.splitlines():
            if "Chat ID:" in line:
                return line.split("Chat ID:")[1].strip()
    logger.error("Chat ID not found in the log file.")
    return None

def main():
    """Main function to execute the summary script."""
    logger.info("Stats script started.")

    summary_time = time.fromisoformat(SUMMARY_TIME)
    
    while True:
        now = datetime.now(tz)
        now_time = now.time().replace(second=0, microsecond=0)
        
        if now_time == summary_time:
            logger.info("Reached summary time.")
            
            # Read log data
            log_data = read_log_file()
            if log_data:
                # Get summary from OpenAI
                summary = send_summary_to_openai(log_data)
                
                if summary:
                    # Get chat ID from the log data
                    chat_id = get_chat_id(log_data)
                    if chat_id:
                        # Send summary to Telegram
                        send_message_to_telegram(chat_id, summary)
            
            # Wait for the next day
            sleep(24 * 60 * 60)
        else:
            # Sleep for a minute and check again
            sleep(60)

if __name__ == "__main__":
    main()
