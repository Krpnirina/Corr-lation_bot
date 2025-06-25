import asyncio
import websockets
import json
from datetime import datetime, timedelta

# ==================== CONFIGURATION ====================
TOKEN = "REzKac9b5BR7DmF"  # ⚠️ Remplacez par votre token démo
APP_ID = 71130
SYMBOL = "R_100"
INITIAL_STAKE = 0.35
TRADE_DURATION = 3  # Durée en minutes
VOLUME_THRESHOLD = 7  # Seuil de volume pour un signal fort
CANDLE_GRANULARITY = 300  # 5 minutes (en secondes)
MAX_TICKS = 10  # Nombre de ticks à collecter
TICKS_TIMEOUT = 30  # Délai d'attente pour les ticks (secondes)

# ==================== FONCTIONS UTILITAIRES ====================
def is_bearish(candle):
    """Vérifie si la bougie est baissière."""
    return candle['open'] > candle['close']

def is_bullish(candle):
    """Vérifie si la bougie est haussière."""
    return candle['close'] > candle['open']

async def collect_ticks(websocket, max_ticks, timeout):
    """Collecte les ticks du marché avec un timeout."""
    ticks = []
    try:
        while len(ticks) < max_ticks:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                data = json.loads(response)
                if data.get("msg_type") == "tick":
                    ticks.append(data["tick"]["quote"])
                    print(f"📊 Tick reçu: {data['tick']['quote']}")
            except asyncio.TimeoutError:
                print("⏳ Délai d'attente dépassé pour les ticks")
                break
    except Exception as e:
        print(f"❌ Erreur lors de la collecte des ticks: {e}")
    return ticks

# ==================== LOGIQUE PRINCIPALE ====================
async def run_bot():
    try:
        print("\n🔌 Connexion à l'API Deriv...")
        async with websockets.connect(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}") as ws:
            
            # === ÉTAPE 1: Authentification ===
            await ws.send(json.dumps({"authorize": TOKEN}))
            auth_response = json.loads(await ws.recv())
            if auth_response.get("error"):
                print(f"❌ Erreur d'authentification: {auth_response['error']['message']}")
                return
            print("✅ Authentification réussie !")

            # === ÉTAPE 2: Récupération des données OHLC ===
            await ws.send(json.dumps({
                "ticks_history": SYMBOL,
                "adjust_start_time": 1,
                "count": 1,
                "end": "latest",
                "granularity": CANDLE_GRANULARITY
            }))
            ohlc_data = json.loads(await ws.recv())
            
            if "history" not in ohlc_data:
                print("❌ Données OHLC non disponibles")
                return

            candle = {
                "open": ohlc_data["history"]["prices"][0],
                "close": ohlc_data["history"]["prices"][-1]
            }
            print(f"📉 Bougie: O={candle['open']} | C={candle['close']}")

            # === ÉTAPE 3: Abonnement aux ticks en temps réel ===
            await ws.send(json.dumps({"ticks": SYMBOL, "subscribe": 1}))
            print("📡 Abonnement aux ticks en cours...")

            # Collecte des ticks
            ticks = await collect_ticks(ws, MAX_TICKS, TICKS_TIMEOUT)
            if not ticks:
                print("⚠️ Aucun tick reçu, annulation du trade")
                return

            # === ÉTAPE 4: Décision de trading ===
            signal_strength = len(ticks)
            direction = None

            if is_bearish(candle):
                direction = "SELL" if signal_strength > VOLUME_THRESHOLD else "BUY"
            elif is_bullish(candle):
                direction = "BUY" if signal_strength > VOLUME_THRESHOLD else "SELL"

            # === ÉTAPE 5: Exécution du trade ===
            if direction:
                print(f"\n🎯 Signal: {'Baissier' if direction == 'SELL' else 'Haussier'}")
                print(f"📈 Force du volume: {signal_strength}/{VOLUME_THRESHOLD}")
                print(f"💸 Placement d'un trade {direction}...")

                trade_params = {
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
                }

                await ws.send(json.dumps(trade_params))
                trade_result = json.loads(await ws.recv())

                if trade_result.get("error"):
                    print(f"❌ Erreur: {trade_result['error']['message']}")
                else:
                    print(f"✅ Trade réussi! ID: {trade_result['buy']['contract_id']}")
            else:
                print("🔍 Aucun signal clair détecté")

    except websockets.ConnectionClosed:
        print("🔌 Connexion interrompue")
    except Exception as e:
        print(f"💥 Erreur critique: {e}")

# ==================== LANCEMENT DU BOT ====================
if __name__ == "__main__":
    print("🚀 Lancement du bot de trading...")
    asyncio.run(run_bot())
