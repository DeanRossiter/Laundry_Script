#!/usr/bin/env python3
import os
import sys
import subprocess

# Virtual Environment Setup
venv_dir = os.path.expanduser("~/laundry-venv")
if not os.path.exists(os.path.join(venv_dir, "bin", "activate")):
    print("Creating virtual environment and installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
    subprocess.check_call([
        os.path.join(venv_dir, "bin", "pip"),
        "install", "--break-system-packages",
        "--upgrade", "pip", "tapo", "requests"
    ])

if sys.prefix != venv_dir:
    activate_script = os.path.join(venv_dir, "bin", "python")
    os.execv(activate_script, [activate_script] + sys.argv)

# Imports
import asyncio
import requests
from tapo import ApiClient

# Pushover Notification
def send_notification(message: str):
    data = {
        "token": "<insert token here>",
        "user":  "<insert user string here>",
        "message": message,
        "sound": "echo" 
    }
    response = requests.post("https://api.pushover.net/1/messages.json", data=data)
    print(f"[NOTIFY] {message} (status {response.status_code})")

# Monitor a single smart plug
async def monitor_plug(plug, label):
    armed = False
    high_power_threshold = 100
    high_power_count = 0
    low_power_threshold = 10
    low_power_count = 0

    while True:
        try:
            energy = await plug.get_energy_usage()
            power = energy.current_power / 1000  # convert mW to W
            print(f"[{label}] Power: {power:.2f} W")

            if power > high_power_threshold:
                high_power_count += 1
                low_power_count = 0
                if not armed and high_power_count >= 10:
                    armed = True
                    print(f"[{label}] Armed (sustained high power)")
            elif power < low_power_threshold:
                high_power_count = 0
                if armed:
                    low_power_count += 1
                    if low_power_count >= 30:
                        send_notification(f"{label} has finished")
                        print(f"[{label}] Disarmed (sustained low power)")
                        armed = False
                        low_power_count = 0
                else:
                    low_power_count = 0
                    high_power_count = 0

        except Exception as e:
            print(f"[{label}] Error reading power: {e}")

        await asyncio.sleep(3)

# Main
async def main():
    email = "<insert email address here>"
    password = "<insert password address here>"
    dryer_ip = "<insert static ip address of dryer smart plug here>"
    washer_ip = "<insert static ip address of washer smart plug here>"

    client = ApiClient(email, password)

    dryer_plug = await client.p110(dryer_ip)
    washer_plug = await client.p110(washer_ip)

    await asyncio.gather(
        monitor_plug(dryer_plug, "Dryer"),
        monitor_plug(washer_plug, "Washer")
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        send_notification(f"Laundry monitor crashed: {e}")
        raise
    finally:
        send_notification("Laundry monitor stopped running.")
