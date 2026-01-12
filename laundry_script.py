class Plug:
    def __init__(self, name, api):
        self.name = name
        self.api = api

#!/usr/bin/env python3
import os
import asyncio
import requests
from tapo import ApiClient
import sys

# ---- Environment Variables ----
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN", "")
PUSHOVER_USER  = os.environ.get("PUSHOVER_USER", "")

TAPO_EMAIL    = os.environ.get("TAPO_EMAIL", "")
TAPO_PASSWORD = os.environ.get("TAPO_PASSWORD", "")

DRYER_IP  = os.environ.get("DRYER_IP", "192.168.1.101")
WASHER_IP = os.environ.get("WASHER_IP", "192.168.1.102")

def check_environment():
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        raise RuntimeError("Missing PUSHOVER_TOKEN or PUSHOVER_USER env vars")

    if not TAPO_EMAIL or not TAPO_PASSWORD:
        raise RuntimeError("Missing TAPO_EMAIL or TAPO_PASSWORD env vars")

# ---- Notifications (quiet unless important) ----
def pushover_sound(machine):
    if machine == "washer":
        return "wm_notification"
    if machine == "dryer":
        return "dry_notification"
    return "echo"

def send_notification(message, machine=None):
    data = {
        "token": PUSHOVER_TOKEN,
        "user":  PUSHOVER_USER,
        "message": message,
        "sound": pushover_sound(machine),
    }
    response = requests.post("https://api.pushover.net/1/messages.json", data=data, timeout=10)
    if response.status_code != 200:
        print(f"Couldn't send message:{message} (status {response.status_code})")

async def notify(message, machine=None):
    await asyncio.to_thread(send_notification, message, machine)

# ---- Monitoring ----
async def monitor_plug(plug):
    
    armed = False
    high_power_threshold = 100
    high_power_count = 0
    low_power_threshold = 10
    low_power_count = 0

    while True:
        try:
            energy = await plug.api.get_current_power()
            power = energy.current_power # / 1000
            print(f"[{plug.name}] Power: {power:.2f} W")
        except Exception as e:
            print("=== Error Reading Power ===")
            print(f"Exception: {e}")
            print(f"Energy: {energy if 'energy' in locals() else 'N/A'}")

        if power > high_power_threshold:
            high_power_count += 1
            low_power_count = 0
            if not armed and high_power_count >= 10:
                armed = True
                print(f"{plug.name} Armed (sustained high power)")

        elif power < low_power_threshold:
            high_power_count = 0
            if armed:
                low_power_count += 1
                if low_power_count >= 60:
                    await notify(f"{plug.name} has finished", plug.name)
                    print(f"{plug.name} Disarmed (sustained low power)")
                    armed = False
                    low_power_count = 0
            else:
                low_power_count = 0

        await asyncio.sleep(3)


async def setup_plugs():
    
    print("=== Connect to client ===")
    client = ApiClient(TAPO_EMAIL, TAPO_PASSWORD)


    print("=== Washer Plug ===")
    try:
        washer_plug = Plug("washer", await client.p110(WASHER_IP))
        washer_connected = True
    except Exception as e:
        washer_connected = False
    
    await asyncio.sleep(3)

    print("=== Dryer Plug ===")
    try:
        dryer_plug = Plug("dryer", await client.p110(DRYER_IP))
        dryer_connected = True
    except Exception as e:
        dryer_connected = False

    print("=== Plug Connection Status ===")
    if not dryer_connected or not washer_connected:
        print(f"Plug connection issue - Dryer status: {dryer_connected}, Washer status: {washer_connected}")
        raise RuntimeError("Could not connect to all plugs")
    print(f"Success - Dryer status: {dryer_connected}, Washer status: {washer_connected}")
    return dryer_plug, washer_plug

# ---- Main ----
async def main():
    print("PYTHON:", sys.executable)
    print("=== Laundry Monitor Started ===")
    
    try:
        print("=== Check Environment ===")
        check_environment()    

        print("=== Initial Notification ===")
        await notify("Laundry monitor power on.")

        print("=== Setup Plugs ===")
        dryer_plug, washer_plug = await setup_plugs()

        print("=== Running Monitor ===")
        await asyncio.gather(
            monitor_plug(dryer_plug),
            monitor_plug(washer_plug),
        )

    except Exception as e:
        try:
            await notify(f"Laundry monitor crashed: {e}")
        except Exception as notify_error:
            print(f"Failed to send crash notification: {notify_error}")


if __name__ == "__main__":
    asyncio.run(main())
