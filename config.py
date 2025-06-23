import os
from dotenv import load_dotenv

# Загружаем .env в переменные окружения
load_dotenv()

# Telegram bot token
BOT_TG_TOKEN = os.getenv("BOT_TG_TOKEN")

# Omega API
OMEGA_API_KEY = os.getenv("OMEGA_API_KEY")

# GitHub Personal Access Token
TOKEN_PAT_REPO_GITHUB = os.getenv("TOKEN_PAT_REPO_GITHUB")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# SSH public keys
ID_ed25519PUB = os.getenv("ID_ed25519PUB")
ID_RSA_PUB = os.getenv("ID_RSA_PUB")
ASPA_VPS_SSH_KEY = os.getenv("ASPA_VPS_SSH_KEY")
# DeepSeek API key
DEEPSEEK = os.getenv("DEEPSEEK")

ID_RSA_PUB_PATH = os.getenv("ID_RSA_PUB_PATH")
