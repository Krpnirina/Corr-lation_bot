import time
from datetime import datetime, timedelta
import random

# --- Configuration ---
TRADE_ASSET = "XAUUSD_OTC"
DURATION_SECONDS = 3600  # 1 ora = 3600 segondra
VOLUME_THRESHOLD = 1.5
TRADE_AMOUNT = 1.0

# --- Simulation data fetch ---
def fetch_mock_data(timeframe):
    """
    Mamerina OHLC, tick_volume, transaction_volume amin'ny fomba simulation.
    Afaka ovaina amin'ny fakana données tena izy raha misy API.
    """
    open_price = round(random.uniform(1930, 1950), 2)
    close_price = round(open_price + random.uniform(-5, 5), 2)
    tick_volume = random.randint(1000, 7000)
    transaction_volume = random.randint(500, 4000)
    return {
        'open': open_price,
        'close': close_price,
        'tick_volume': tick_volume,
        'transaction_volume': transaction_volume
    }

def candle_direction(open_p, close_p):
    if close_p > open_p:
        return "bullish"
    elif close_p < open_p:
        return "bearish"
    else:
        return "neutral"

def is_tick_strong(tick_vol, trans_vol):
    if trans_vol == 0:
        return False
    return (tick_vol / trans_vol) >= VOLUME_THRESHOLD

def decide_trade(data_m15, data_m30, data_h1):
    dir_m15 = candle_direction(data_m15['open'], data_m15['close'])
    dir_m30 = candle_direction(data_m30['open'], data_m30['close'])
    dir_h1 = candle_direction(data_h1['open'], data_h1['close'])

    print(f"[INFO] Directions M15: {dir_m15}, M30: {dir_m30}, H1: {dir_h1}")

    if not (dir_m15 == dir_m30 == dir_h1):
        print("[INFO] Directions tsy mitovy, tsy manao trade.")
        return None

    avg_tick_vol = (data_m15['tick_volume'] + data_m30['tick_volume'] + data_h1['tick_volume']) / 3
    avg_trans_vol = (data_m15['transaction_volume'] + data_m30['transaction_volume'] + data_h1['transaction_volume']) / 3
    strong_tick = is_tick_strong(avg_tick_vol, avg_trans_vol)

    print(f"[INFO] Avg tick vol: {avg_tick_vol:.2f}, Avg trans vol: {avg_trans_vol:.2f}, Tick strong? {strong_tick}")

    # Logic trading araka ny fangatahanao:
    if strong_tick and dir_m15 == "bullish":
        return "BUY"
    elif strong_tick and dir_m15 == "bearish":
        return "SELL"
    elif not strong_tick and dir_m15 == "bearish":
        return "BUY"
    elif not strong_tick and dir_m15 == "bullish":
        return "SELL"
    else:
        print("[INFO] Tsy misy conditions feno.")
        return None

def main_loop():
    print("[BOT] Manomboka 24/24. Manangona data...")
    start_time = datetime.now()

    data_collection = []

    while True:
        now = datetime.now()
        elapsed = (now - start_time).total_seconds()

        # Maka data simulation amin'ny timeframes
        data_m15 = fetch_mock_data("M15")
        data_m30 = fetch_mock_data("M30")
        data_h1 = fetch_mock_data("H1")

        data_collection.append((data_m15, data_m30, data_h1))

        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Nanangona data faha-{len(data_collection)} (Elapsed: {int(elapsed)} segondra)")

        # Raha mbola tsy feno 1h ny data dia mitohy manangona fotsiny
        if elapsed < DURATION_SECONDS:
            print("[INFO] Tsy mbola feno 1 ora ny fanangonana data, mbola miandry...")
            time.sleep(1)
            continue

        # Raha feno 1 ora, manomboka analyse isaky ny segondra rehefa misy data vaovao
        decision = decide_trade(data_m15, data_m30, data_h1)

        if decision:
            print(f"[TRADE] Manao {decision} amin'ny vola: {TRADE_AMOUNT} amin'ny asset {TRADE_ASSET}")
            # Eto no atao ny placement automatique raha misy API
            # Raha tsy izany dia simulation fotsiny
        else:
            print("[TRADE] Tsy manao position amin'izao fotoana izao.")

        # Reset start_time ho an'ny cycle manaraka
        start_time = datetime.now()
        data_collection.clear()

        print("[BOT] Manomboka fanangonana vaovao manaraka...")
        time.sleep(1)

if __name__ == "__main__":
    main_loop()