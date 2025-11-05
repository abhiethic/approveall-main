import os
from typing import List

API_ID = os.environ.get("API_ID", "28614709")
API_HASH = os.environ.get("API_HASH", "f36fd2ee6e3d3a17c4d244ff6dc1bac8")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7938087417:AAHlOKaw_XPTlfET_qwfq2USmnFsJaKi5gA")
ADMIN = int(os.environ.get("ADMIN", "8238941133"))

# Set to None to disable or provide a valid channel ID
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002669902570")) if os.environ.get("LOG_CHANNEL") else None
NEW_REQ_MODE = os.environ.get("NEW_REQ_MODE", "True").lower() == "true"

DB_URI = os.environ.get("DB_URI", "mongodb+srv://ZeroTwo:aloksingh@zerotwo.3q3ij.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.environ.get("DB_NAME", "Approve")

IS_FSUB = os.environ.get("IS_FSUB", "False").lower() == "true"
AUTH_CHANNELS = list(map(int, filter(None, os.environ.get("AUTH_CHANNEL", "").split())))
