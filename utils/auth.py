from functools import wraps
from flask import session, jsonify
import os


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = session.get("api_key")
        if not api_key:
            return jsonify({"error": "需要API密钥"}), 401
        return f(*args, **kwargs)

    return decorated_function


def validate_api_key(api_key):
    """验证API密钥"""
    try:
        # 这里可以添加更多的验证逻辑
        if not api_key or len(api_key.strip()) < 10:
            return False
        return True
    except Exception as e:
        print(f"API密钥验证错误: {str(e)}")
        return False


def get_api_key():
    """获取当前API密钥"""
    return session.get("api_key") or os.environ.get("OPENAI_API_KEY")
