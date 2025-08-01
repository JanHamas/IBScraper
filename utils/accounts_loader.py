from pathlib import Path
import json, asyncio
from aioconsole import ainput


# Get the accounts dir
BAISE_DIR = Path(__file__).resolve().parent
ACCOUNTS_DIR = BAISE_DIR / "accounts"

async def load_accounts():
    list_of_accounts = []
    try:
        for account in ACCOUNTS_DIR.glob("*.json"):
            with open(account, "r") as f:
                account = json.load(f)            
        print(f"✔ Sucessfully {len(list_of_accounts)} indeed accounts load")
        return account
    except Exception as e:
        print(f"❌ Error accounts loading: \n {e}")



if __name__ == "__main__":
    asyncio.run(load_accounts())

