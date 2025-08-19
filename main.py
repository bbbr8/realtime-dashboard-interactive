from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
import httpx



app = FastAPI()

# Serve static files
base_path = Path(__file__).resolve().parent
static_dir = base_path / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Store the latest data for earthquakes, weather and crypto
data_store = {
    "earthquakes": [],
    "weather": {},
    "crypto": {}
}

clients = set()

async def fetch_feeds():
    """Background task to fetch public feeds every 60 seconds and broadcast updates."""
    while True:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Fetch earthquake feed
                eq_resp = await client.get(
                    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
                )
                if eq_resp.status_code == 200:
                    eq_json = eq_resp.json()
                    quakes = []
                    for feature in eq_json.get("features", []):
                        mag = feature["properties"].get("mag")
                        place = feature["properties"].get("place")
                        quakes.append(f"M{mag} – {place}")
                    data_store["earthquakes"] = quakes

                
                # Fetch weather feed (Salt Lake City by default)
                weather_resp = await client.get("https://wttr.in/Salt%20Lake%20City?format=j1")
                if weather_resp.status_code == 200:
                    w_json = weather_resp.json()
                    current = w_json.get("current_condition", [{}])[0]
                    data_store["weather"] = {
                        "temp_c": current.get("temp_C"),
                        "humidity": current.get("humidity"),
                        "desc": current.get("weatherDesc", [{}])[0].get("value")
                    }

                # Fetch Bitcoin price
                btc_resp = await client.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json")
                if btc_resp.status_code == 200:
                    btc_json = btc_resp.json()
                    usd = btc_json["bpi"]["USD"]
                    data_store["crypto"] = {
                        "rate": usd["rate"],
                        "updated": btc_json["time"]["updated"]
                    }

                # Broadcast the latest data to all connected WebSocket clients
                for ws in list(clients):
                    try:
                        await ws.send_json(data_store)
                    except WebSocketDisconnect:
                        clients.discard(ws)
        except Exception as exc:
            # Log network failures and continue
            print(f"Error fetching feeds: {exc}")
        await asyncio.sleep(60)
        

@app.on_event("startup")
async def start_fetcher():
    # Start the background feed fetcher
    asyncio.create_task(fetch_feeds())

@app.get("/")
async def get_index():
    # Return the dashboard page
    index_file = static_dir / "index.html"
    return HTMLResponse(index_file.read_text())

@app.get("/data")

async def get_current_data():
    """Return the current data without waiting for the WebSocket broadcast."""
    return JSONResponse(data_store)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        # Send the current data immediately on connection
        await websocket.send_json(data_store)
        while True:
            await websocket.receive_text()  # keep the connection open
    except WebSocketDisconnect:
        clients.discard(websocket)
