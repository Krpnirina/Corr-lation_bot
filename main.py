import asyncio
import websockets
import json
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOKEN = os.getenv("DERIV_TOKEN") or "REzKac9b5BR7DmF"
APP_ID = 71130
SYMBOL = "R_100"
INITIAL_STAKE = 0.35
TRADE_DURATION = 3  # in minutes
VOLUME_THRESHOLD = 7  # number of ticks to consider strong volume
CANDLE_GRANULARITY = 300  # 5 minutes

# --- UTILS ---
def is_bearish(candle):
    return candle['open'] > candle['close']

def is_bullish(candle):
    return candle['close'] > candle['open']

# --- MAIN FUNCTION ---
async def run_bot():
    url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    async with websockets.connect(url) as ws:
        print("🔌 Connecting to Deriv WebSocket...")

        await ws.send(json.dumps({
            "authorize": TOKEN
        }))
        auth_response = json.loads(await ws.recv())
        if auth_response.get("error"):
            print(f"❌ Authorization error: {auth_response['error']['message']}")
            return
        print("✅ Authorized")

        # Fetch 1 candle of 5-minute timeframe
        await ws.send(json.dumps({
            "ticks_history": SYMBOL,
            "adjust_start_time": 1,
            "count": 1,
            "end": "latest",
            "granularity": CANDLE_GRANULARITY
        }))
        ohlc_response = json.loads(await ws.recv())
        try:
            prices = ohlc_response['history']['prices']
            times = ohlc_response['history']['times']
        except KeyError:
            print(f"❌ Error fetching OHLC: {ohlc_response}")
            return

        candle = {
            "open": prices[0],
            "close": prices[-1],
        }

        # Collect last 10 ticks
        await ws.send(json.dumps({
            "ticks": SYMBOL,
            "subscribe": 1
        }))

        ticks = []
        print(f"📥 Subscribed to tick data for {SYMBOL}")
        while len(ticks) < 10:
            tick_msg = json.loads(await ws.recv())
            if tick_msg['msg_type'] == "tick":
                tick = tick_msg['tick']['quote']
                ticks.append(tick)
                print(f"📊 Tick: {tick}")

        # Unsubscribe from tick stream
        await ws.send(json.dumps({"forget_all": "ticks"}))

        # Decision logic
        volume_strength = len(ticks)
        direction = None

        if is_bearish(candle):
            if volume_strength > VOLUME_THRESHOLD:
                direction = "SELL"
            else:
                direction = "BUY"
        elif is_bullish(candle):
            if volume_strength > VOLUME_THRESHOLD:
                direction = "BUY"
            else:
                direction = "SELL"

        if direction:
            print(f"🧠 Candle analysis: {'Bearish' if is_bearish(candle) else 'Bullish'}")
            print(f"📈 Volume strength: {volume_strength}")
            print(f"🟢 Placing trade: {direction}")

            await ws.send(json.dumps({
                "buy": 1,
                "price": INITIAL_STAKE,
                "parameters": {
                    "amount": INITIAL_STAKE,
                    "basis": "stake",
                    "contract_type": "CALL" if direction == "BUY" else "PUT",
                    "currency": "USD",
                    "duration": TRADE_DURATION,
                    "duration_unit": "m",
                    "symbol": SYMBOL
                }
            }))
            response = json.loads(await ws.recv())
            if response.get("error"):
                print(f"❌ Trade error: {response['error']['message']}")
            else:
                print(f"✅ Trade placed: {response['buy']['contract_id']}")
        else:
            print("⚠️ No clear signal to trade.")

# --- EXECUTE ---
asyncio.run(run_bot())
