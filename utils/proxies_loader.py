import asyncio
import os


# get the current dir path 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROXIES_FILE = os.path.join(BASE_DIR,"proxies.txt")

async def load_proxies():
    try:
        proxies = []
        with open(PROXIES_FILE, "r") as f:
            for proxy in f:
                parts = proxy.strip().split(":")
                if len(parts) == 4:
                    ip, port, user, pwd = parts
                    proxies.append({
                        "server": f"http://{ip}:{port}",
                        "username": user,
                        "password": pwd
                    })
        return proxies
    except Exception as e:
        print(f"❌ Error \n {e}")
    