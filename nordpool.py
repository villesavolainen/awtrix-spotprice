#!/usr/bin/env python3
import requests
import json
import datetime
import pytz
import paho.mqtt.client as mqtt
import time
import logging
import os

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration from environment variables with defaults
MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt_broker_address")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "awtrix/custom/nordpool")
NORDPOOL_API_URL = os.environ.get("NORDPOOL_API_URL", "https://api.spot-hinta.fi/JustNow")
NORDPOOL_DAY_AHEAD_URL = os.environ.get("NORDPOOL_DAY_AHEAD_URL", "https://api.spot-hinta.fi/Today")
TIMEZONE = os.environ.get("TIMEZONE", "Europe/Helsinki")
UPDATE_INTERVAL = int(os.environ.get("UPDATE_INTERVAL", 300))
BAR_CHART_OFFSET = int(os.environ.get("BAR_CHART_OFFSET", 9))
COLOR_THRESHOLDS = json.loads(os.environ.get("COLOR_THRESHOLDS", '{"0": "#00FF00", "8": "#FFFF00", "16": "#FF0000"}'))

logger.info(f"COLOR_THRESHOLDS: {COLOR_THRESHOLDS}")

# Cache for day-ahead prices
hourly_prices_cache = {
    "data": None,
    "timestamp": None,
    "next_update_time": None
}

def get_nordpool_price():
    """Fetch the current Nordpool spot price"""
    try:
        response = requests.get(NORDPOOL_API_URL)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Price is in euros/kWh
        price = data.get("PriceNoTax", 0)
        
        # Convert to cents/kWh for easier reading
        price_cents = price * 100
        
        logger.info(f"Current spot price: {price} €/kWh ({price_cents:.2f} cents/kWh)")
        logger.info(f"Price: {price_cents}, Color: {get_price_color(price_cents)}")
        return price_cents
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Nordpool price: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing Nordpool data: {e}")
        return None

def get_day_ahead_prices():
    """
    Fetch the day-ahead prices for all 24 hours with caching
    Prices are updated daily around 14:00, so we'll cache them until then
    """
    now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    
    # Check if we need to update the cache
    if (hourly_prices_cache["data"] is not None and 
        hourly_prices_cache["next_update_time"] is not None and 
        now < hourly_prices_cache["next_update_time"]):
        logger.debug("Using cached hourly prices")
        return hourly_prices_cache["data"]
    
    try:
        logger.info("Fetching new day-ahead prices")
        response = requests.get(NORDPOOL_DAY_AHEAD_URL)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Create a dictionary to map hour to price
        hour_to_price = {}
        
        for hour_data in data:
            # Extract timestamp and price
            timestamp_str = hour_data.get("DateTime")
            price = hour_data.get("PriceNoTax", 0) * 100  # Convert to cents
            
            # Parse timestamp to get hour
            if timestamp_str:
                timestamp = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp = timestamp.astimezone(pytz.timezone(TIMEZONE))
                hour = timestamp.hour
                hour_to_price[hour] = price
        
        # Create ordered list of prices for all 24 hours
        hourly_prices = []
        for hour in range(24):
            if hour in hour_to_price:
                hourly_prices.append(hour_to_price[hour])
            else:
                # If we don't have data for this hour, use None or a default value
                hourly_prices.append(None)
        
        # Calculate next update time (today at 14:05 or tomorrow if it's already past 14:05)
        next_update = now.replace(hour=14, minute=5, second=0, microsecond=0)
        if now >= next_update:
            next_update = next_update + datetime.timedelta(days=1)
        
        # Update cache
        hourly_prices_cache["data"] = hourly_prices
        hourly_prices_cache["timestamp"] = now
        hourly_prices_cache["next_update_time"] = next_update
        
        logger.info(f"Fetched day-ahead prices for {len(hourly_prices)} hours, next update at {next_update}")
        return hourly_prices
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching day-ahead prices: {e}")
        # Return cached data if available, even if it's outdated
        if hourly_prices_cache["data"] is not None:
            logger.warning("Using outdated cached hourly prices due to API error")
            return hourly_prices_cache["data"]
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing day-ahead data: {e}")
        # Return cached data if available, even if it's outdated
        if hourly_prices_cache["data"] is not None:
            logger.warning("Using outdated cached hourly prices due to parsing error")
            return hourly_prices_cache["data"]
        return None

def get_price_color(price):
    """
        Determine color based on price thresholds with smooth transitions between thresholds.
        
        Args:
            price (float): The price value to evaluate
            
        Returns:
            str: Hex color code based on the threshold the price falls into,
                 with smooth transitions between threshold colors
    """
    # Convert threshold keys to float and sort them in ascending order
    thresholds = sorted([float(threshold) for threshold in COLOR_THRESHOLDS.keys()])
    
    # If price is below the lowest threshold, use the lowest threshold color
    if price < thresholds[0]:
        threshold_key = str(int(thresholds[0])) if thresholds[0] == int(thresholds[0]) else str(thresholds[0])
        return COLOR_THRESHOLDS[threshold_key]
    
    # If price is above the highest threshold, use the highest threshold color
    if price >= thresholds[-1]:
        threshold_key = str(int(thresholds[-1])) if thresholds[-1] == int(thresholds[-1]) else str(thresholds[-1])
        return COLOR_THRESHOLDS[threshold_key]
    
    # Find the two thresholds that the price falls between
    lower_threshold = None
    upper_threshold = None
    
    for i in range(len(thresholds) - 1):
        if thresholds[i] <= price < thresholds[i + 1]:
            lower_threshold = thresholds[i]
            upper_threshold = thresholds[i + 1]
            break
    
    # If we couldn't find appropriate thresholds, use the default color
    if lower_threshold is None or upper_threshold is None:
        threshold_key = str(int(thresholds[0])) if thresholds[0] == int(thresholds[0]) else str(thresholds[0])
        return COLOR_THRESHOLDS[threshold_key]
    
    # Convert thresholds to string keys for the COLOR_THRESHOLDS dictionary
    lower_key = str(int(lower_threshold)) if lower_threshold == int(lower_threshold) else str(lower_threshold)
    upper_key = str(int(upper_threshold)) if upper_threshold == int(upper_threshold) else str(upper_threshold)
    
    # Get the colors for the lower and upper thresholds
    lower_color = COLOR_THRESHOLDS[lower_key]
    upper_color = COLOR_THRESHOLDS[upper_key]
    
    # Calculate how far between the thresholds the price is (0.0 to 1.0)
    ratio = (price - lower_threshold) / (upper_threshold - lower_threshold)
    
    # Blend the colors based on the ratio
    blended_color = blend_colors(lower_color, upper_color, ratio)
    
    logger.debug(f"Price {price} is between {lower_threshold} and {upper_threshold}, " 
                f"ratio: {ratio:.2f}, blended color: {blended_color}")
    
    return blended_color
    
def blend_colors(color1, color2, ratio):
    """
    Blend two hex colors based on a ratio.
    
    Args:
        color1 (str): First hex color code (e.g., "#00FF00")
        color2 (str): Second hex color code (e.g., "#FF0000")
        ratio (float): Blend ratio from 0.0 (100% color1) to 1.0 (100% color2)
    
    Returns:
        str: Blended hex color code
    """
    # Ensure ratio is between 0 and 1
    ratio = max(0, min(1, ratio))
    
    # Convert hex colors to RGB
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
    
    # Blend the colors
    r = int(r1 * (1 - ratio) + r2 * ratio)
    g = int(g1 * (1 - ratio) + g2 * ratio)
    b = int(b1 * (1 - ratio) + b2 * ratio)
    
    # Convert back to hex
    return f"#{r:02x}{g:02x}{b:02x}"

def create_hourly_bar(hourly_prices):
    """
    Create a bar chart visualization for hourly prices
    Draws a full 24-hour bar chart starting from the specified offset
    """
    if not hourly_prices or len(hourly_prices) == 0:
        return None
    
    # Get current hour
    now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    current_hour = now.hour
    
    # Create bar chart with dots for each hour
    bar_chart = []
    
    # Use the configured offset for the bar chart
    offset_pixels = BAR_CHART_OFFSET
    
    # Draw each hour's price as a colored dot
    for hour in range(24):
        # Get price for this hour (handle None values)
        if hour < len(hourly_prices) and hourly_prices[hour] is not None:
            price = hourly_prices[hour]
            color = get_price_color(price)
        else:
            # Use a default color for missing data
            color = "#333333"  # Dark gray
        
        # Draw pixel command for each hour
        dot = {
            "dp": [offset_pixels + hour, 7, color]  # dp = Draw Pixel at [x, y, color]
        }
        bar_chart.append(dot)
    
    # Add current hour indicator (purple dot one row above)
    if 0 <= current_hour < 24:
        current_hour_indicator = {
            "dp": [offset_pixels + current_hour, 6, "#800080"]  # Purple dot
        }
        bar_chart.append(current_hour_indicator)
        
    return bar_chart

def format_awtrix_message(price, hourly_prices=None):
    """Format the price for Awtrix display"""
    if price is None:
        return None
    
    # Get current time for the message
    now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    time_str = now.strftime("%H:%M")
    
    # Format price to 2 decimal places (price is already in cents)
    price_str = f"{price:.2f}"
    
    # Create Awtrix message
    awtrix_message = {
        "text": f"{price_str} c",
        "textCase": "2",
        "icon": "54077",  # Lightning bolt icon (you can change this)
        "color": "#00FF00",  # Green color for the text (default)
        "rainbow": False,
        "duration": 3,  # Display duration in seconds
        "scrollSpeed": 100,  # Scroll speed
    }
    
    # Change color based on price according to thresholds (price is in cents)
    awtrix_message["color"] = get_price_color(price)
    
    # Add hourly bar chart if available
    if hourly_prices:
        bar_chart = create_hourly_bar(hourly_prices)
        if bar_chart:
            awtrix_message["draw"] = bar_chart
    
    return json.dumps(awtrix_message)

def publish_to_awtrix(mqtt_client, message):
    """Publish the message to Awtrix via MQTT"""
    if message is None:
        return
    
    try:
        mqtt_client.publish(MQTT_TOPIC, message)
        logger.info(f"Published to {MQTT_TOPIC}: {message}")
    except Exception as e:
        logger.error(f"Error publishing to MQTT: {e}")

def main():
    """Main function to run the program"""
    # Connect to MQTT broker
    mqtt_client = mqtt.Client(client_id="NordpoolClient")
    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        return
    
    try:
        while True:
            # Get current price
            price = get_nordpool_price()
            
            # Get day-ahead prices for all hours
            hourly_prices = get_day_ahead_prices()
            print(f"hourly_prices: {hourly_prices}")
            
            # Format and publish message
            message = format_awtrix_message(price, hourly_prices)
            publish_to_awtrix(mqtt_client, message)
            print(message)
            # Wait for next update
            time.sleep(UPDATE_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("Disconnected from MQTT broker")

if __name__ == "__main__":
    main()