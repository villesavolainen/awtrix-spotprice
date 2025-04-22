# Nordpool MQTT Service

## Description

This service retrieves electricity price data from Nordpool and publishes it to an MQTT broker. It's designed to run as a containerized service using Docker, making it easy to deploy and integrate with home automation systems or other applications that need real-time electricity pricing information.

The service:
- Fetches current and future electricity prices from Nordpool
- Processes and formats the pricing data
- Publishes the data to configurable MQTT topics
- Runs on a schedule to keep pricing information up-to-date

## Features

- Containerized deployment with Docker
- Integrated Mosquitto MQTT broker
- Configurable data retrieval intervals
- Persistent MQTT message storage
- Comprehensive logging

## Prerequisites

- Docker
- Docker Compose
- Internet connection (for fetching Nordpool data)
- Basic understanding of MQTT (for consuming the published data)

## Installation & Deployment

### Quick Start

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/nordpool-mqtt.git
   cd nordpool-mqtt
   ```