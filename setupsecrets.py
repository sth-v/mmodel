


def setup_secrets(update=False):
    import json, subprocess, base64, shutil, os

    if update or not os.path.isfile("env.json"):
        subprocess.Popen(["git", "clone", "https://github.com/contextmachine/secrets.git"])
        shutil.move("secrets/env.json", "env.json")
    with open("env.json", "r") as f:
        data = json.load(f)
        data["CADEX_LICENSE"] = base64.b64decode(data["CADEX_LICENSE"]).decode()
        for k in data.keys():
            os.environ[k] = str(data[k])
        return data
