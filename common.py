import json
import os
import pickle
import traceback

kokocreditdefaulturl = "https://estore.kokoamusement.com.au/BalanceMobile/BalanceMobile.aspx?i="
repositoryurl = "https://github.com/etangaming123/etanbot"
developergithub = "https://github.com/etangaming123"

datastores = ["linkedkokocards", "profiles"]
datastoresbuttheseonesarelists = []

def ensure_datastores():
    for item in datastores:
        if os.path.exists(f"{item}.pkl"):
            data = pickle.load(open(f"{item}.pkl", "rb"))
            with open(f"{item}.json", "w") as file:
                json.dump(data, file, indent=4)
                print(f"Converted [{item}.pkl] to [{item}.json]")
        if not os.path.exists(f"{item}.json"):
            with open(f"{item}.json", "w") as file:
                json.dump({}, file)
            print(f"Created new file [{item}.json]")

    for item in datastoresbuttheseonesarelists:
        if os.path.exists(f"{item}.pkl"):
            data = pickle.load(open(f"{item}.pkl", "rb"))
            with open(f"{item}.json", "w") as file:
                json.dump(data, file, indent=4)
                print(f"Converted [{item}.pkl] to [{item}.json]")
        if not os.path.exists(f"{item}.json"):
            with open(f"{item}.json", "w") as file:
                json.dump([], file)
            print(f"Created new file [{item}.json]")

def saveData(store: str, newdata: dict):
    print(f"Saving [{store}]...")
    try:
        backup = loadData(store)
        with open(f"{store}_backup.json", "w") as file:
            json.dump(backup, file)
        with open(f"{store}.json", "w") as file:
            json.dump(newdata, file)
        os.remove(f"{store}_backup.json")
        return True
    except Exception:
        traceback.print_exc()
        with open(f"{store}.json", "w") as file:
            json.dump(backup, file)
        return False

def loadData(store: str):
    try:
        with open(f"{store}.json", "r") as file:
            return json.load(file)
    except Exception:
        traceback.print_exc()
        return ""