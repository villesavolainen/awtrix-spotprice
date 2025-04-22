# Nordpool Spot Price Display for Awtrix

This project fetches electricity spot prices from the Nordpool market and displays them on an Awtrix LED matrix display. It shows the current price with color coding and a 24-hour price chart to help visualize price trends throughout the day.

## Features

- Real-time electricity spot price display in cents/kWh
- Color-coded prices based on configurable thresholds
- 24-hour price chart with current hour indicator
- Automatic updates at configurable intervals
- Docker-based deployment for easy setup

## Prerequisites

- Docker and Docker Compose
- An Awtrix LED matrix display on your network
- Internet connection to fetch Nordpool prices

## Installation

### 1. Install Docker and Docker Compose

#### Docker
- **Windows/Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/)

#### Docker Compose
- **Docker Compose V1** (docker-compose command): [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Docker Compose V2** (docker compose plugin): Included with recent Docker Desktop installations or [install the plugin](https://docs.docker.com/compose/install/linux/)

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/awtrix-spotprice.git
cd awtrix-spotprice
```

### 3. Configuration Options

Edit the docker-compose.yaml file to customize your configuration

```
environment:
  - MQTT_BROKER=mqtt
  - MQTT_PORT=1883
  - MQTT_TOPIC=awtrix/custom/nordpool # Configure your Awtrix to use this topic
  - UPDATE_INTERVAL=300  # Update interval in seconds
  - BAR_CHART_OFFSET=9  # X-position where the bar chart starts
  - COLOR_THRESHOLDS={"0": "#00FF00", "8": "#FFFF00", "16": "#FF0000"}  # Price thresholds in cents/kWh
```

### 4. Build and start the containers

#### Docker Compose V1
docker-compose up -d

# Check the logs
docker-compose logs -f nordpool

# Stop the containers
docker-compose down

#### Docker Compose V2
# Build and start the containers
docker compose up -d

# Check the logs
docker compose logs -f nordpool

# Stop the containers
docker compose down


## Configuration variables
Environment Variables for Nordpool Spot Price Display
The following table lists all environment variables that can be configured for the Nordpool Spot Price Display application:
| Environment Variable | Description | Default Value | Example |
|----------------------|-------------|---------------|---------|
| `MQTT_BROKER` | MQTT broker address | "mqtt_broker_address" | "mqtt" or "192.168.1.100" |
| `MQTT_PORT` | MQTT broker port | 1883 | 1883 |
| `MQTT_TOPIC` | MQTT topic for Awtrix | "awtrix/custom/nordpool" | "awtrix/custom/electricity" |
| `NORDPOOL_API_URL` | API URL for current price | "https://api.spot-hinta.fi/JustNow" | "https://alternative-api.com/current" |
| `NORDPOOL_DAY_AHEAD_URL` | API URL for day-ahead prices | "https://api.spot-hinta.fi/Today" | "https://alternative-api.com/today" |
| `TIMEZONE` | Timezone for price data | "Europe/Helsinki" | "Europe/Stockholm" |
| `UPDATE_INTERVAL` | Update interval in seconds | 300 | 600 |
| `BAR_CHART_OFFSET` | X-position where the bar chart starts | 9 | 8 |
| `COLOR_THRESHOLDS` | JSON object mapping price thresholds to colors | '{"0": "#00FF00", "8": "#FFFF00", "16": "#FF0000"}' | '{"0": "#0000FF", "5": "#00FF00", "10": "#FFFF00", "20": "#FF0000"}' |