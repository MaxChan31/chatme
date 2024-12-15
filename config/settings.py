import os

# 基础配置
DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")

# API配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-3.5-turbo"
MAX_CONVERSATION_HISTORY = 100

# 数据库配置（如果需要）
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///chat.db")

# 缓存配置
CACHE_TYPE = "simple"
CACHE_DEFAULT_TIMEOUT = 300

# 安全配置
SESSION_COOKIE_SECURE = True
PERMANENT_SESSION_LIFETIME = 86400  # 24小时

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
