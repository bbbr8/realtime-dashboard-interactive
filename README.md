# Real-Time Data Dashboard (Interactive)

This project is an interactive real-time dashboard built with FastAPI and vanilla JavaScript. It aggregates data from free public APIs and provides a click-to-refresh interface along with automatic WebSocket updates.

## Features

- **Earthquakes:** Retrieves a list of earthquakes from the past hour using the USGS GeoJSON feed and displays magnitude and location.
- **Weather:** Shows current weather conditions for Salt Lake City, including temperature, humidity and description, fetched from `wttr.in`.
- **Bitcoin price:** Displays the current Bitcoin price in USD using the Coindesk API.
- **Click to refresh:** Each section has a button to fetch the latest data on demand via a simple REST call.
- **Automatic updates:** A background task on the server polls each feed every minute and broadcasts updates to all connected browsers via WebSockets.
- **WebSocket reconnection:** If the WebSocket closes, the client automatically attempts to reconnect.

## Running locally

1. Clone this repository:
   ```
   git clone https://github.com/bbbr8/realtime-dashboard-interactive.git
   cd realtime-dashboard-interactive
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the server:
   ```
   uvicorn main:app --reload
   ```
4. Open `http://localhost:8000` in your browser. Use the "Refresh Now" buttons to request the latest data. The page will also update automatically as new data is fetched.

## How it works

The `main.py` file defines a FastAPI application that serves the static dashboard page and exposes two endpoints:

- `/data` (GET) – returns the current earthquake, weather and crypto data.
- `/ws` (WebSocket) – streams data to clients whenever the server refreshes the feeds.

On startup, the app launches a background task (`fetch_feeds`) that fetches:
- The USGS earthquake feed: https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
- Weather for Salt Lake City: https://wttr.in/Salt%20Lake%20City?format=j1
- Bitcoin price: https://api.coindesk.com/v1/bpi/currentprice/BTC.json

Results are stored in an in-memory dictionary and broadcast to connected WebSocket clients. The front-end code (`static/index.html`) establishes the WebSocket, updates the UI when messages arrive, and provides buttons to call `/data` to fetch on demand.
