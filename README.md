# jkbms-battery-monitoring

This project is designed to monitor and analyze the charge state of a battery using a JKBMS board and Raspberry Pi, providing insights and updates via a Telegram bot. 

## Introduction

The `jkbms-battery-monitoring` project leverages a Raspberry Pi and a JKBMS board to monitor battery status. It logs battery data and sends periodic summaries to a Telegram bot using OpenAI's API. The use of Docker containers ensures isolation and ease of deployment.

## Prerequisites

- **Hardware**: Raspberry Pi with Bluetooth capability and the JKBMS integrated into your battery system.
- **Software**: Docker and Docker Compose installed on the Raspberry Pi.
- **API Keys**:
  - Obtain an OpenAI API key from [OpenAI](https://beta.openai.com/signup/).
  - Create a Telegram bot and get the bot token from [BotFather](https://core.telegram.org/bots#botfather).

## Installation

To set up the project, follow these steps:

1. **Install Docker and Docker Compose**:
   - Follow the official Docker documentation to install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

2. **Install Bleak on the Host Machine**:
   - `bleak` is required on the host machine for Bluetooth communication. You can install it using pip:
```sh
pip install bleak
```

3. **Clone the repository**:
```bash
git clone https://github.com/denyslietnikov/jkbms-battery-monitoring.git
cd jkbms-battery-monitoring
```

4. **Set up environment variables**:

   - Create a .env file for each service (battery-monitor and battery-statistics) using the examples provided below.

### battery-monitor

This service monitors the battery status and logs data to a file. It uses the following environment variables:

**.env example**:  
TELEGRAM_BOT_TOKEN=  
CHECK_INTERVAL=600  
POLLING_INTERVAL=60  
DEVICE_MAC=C8:47:80:12:AD:6E  
DEVICE_NAME=JK_B1A8S20P  
DEVICE_PROTOCOL=JK02  
LOG_HTTP_REQUESTS=False  
LOG_FILE_PATH=/logs/stat.log  
TIMEZONE=UTC 
MIN_VOLTAGE=20  
MAX_VOLTAGE=25  


### battery-statistics:
 
This service analyzes the logged battery data and sends a summary to a Telegram bot using OpenAI's API. 

**.env example**:  
OPENAI_API_KEY=  
DATA_LOG_FILE=/logs/stat.log  
SUMMARY_TIME=23:59  
TELEGRAM_BOT_TOKEN=  
OPENAI_MODEL=gpt-4o-mini  
OPENAI_PROMPT=Analyze how the battery charge changed over the course of a day. The possible states of the battery are: charged (charge is 99% or higher, and may fluctuate between 99% and 105%), slowly discharging (used for autonomous power supply to appliances, with a prolonged decrease in charge falling below 90% until the battery starts charging again), or charging from the city grid, gradually accumulating charge (several consecutive measurements show a noticeable increase). The switch to autonomous power supply can happen several times a day. Indicate the number of switches to autonomous power supply and, for each case, specify when the battery was fully charged after the use of autonomous power. Return only the text with filled values (date format 25-12-2024, time format 00:00): "Statistics for [date]. Autonomous power was used [number] times during the day, the minimum charge was [value]% recorded at [time], the battery was fully charged at [time1], [time2], ...".  
TIMEZONE=UTC 

5. **Start the Docker Containers**:
   - Navigate to the directory containing your `docker-compose.yml` file and run:
```sh
docker-compose up -d
```

This setup ensures that the `battery-monitor` service logs the battery data and the `battery-statistics` service analyzes the data and sends a summary via Telegram.

## Usage

- **Start Monitoring**:
  - Send the `/start` command to the Telegram bot to begin monitoring the battery status.

- **Logs and Analysis**:
  - The `battery-monitor` service will continuously log battery data.
  - At the specified `SUMMARY_TIME`, the `battery-statistics` service will read the log file, analyze the data, and send a summary to the Telegram bot.

## Inspiration

This project was inspired by the article [Monitor Your JKBMS from Anywhere Over the Internet](https://sysopstechnix.com/monitor-your-jkbms-from-anywhere-over-the-internet/).
For more details on using the jkbms command, refer to the [jkbms usage page](https://github.com/jblance/mpp-solar/wiki/Detailed-Usage#jkbms-usage).

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests.


Feel free to reach out if you have any questions or need further assistance. Happy monitoring!