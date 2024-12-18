from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    copy_current_request_context,
    send_from_directory,
)
import os
import requests
from datetime import datetime
import socket
from threading import Thread
from werkzeug.middleware.shared_data import SharedDataMiddleware

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 添加静态文件中间件
app.wsgi_app = SharedDataMiddleware(
    app.wsgi_app,
    {
        "/": os.path.join(
            os.path.dirname(__file__), "static"
        )  # 将static目录映射到根路径
    },
)

# 密码到API密钥的映射
API_PASSWORD_MAP = {
    "CMK1213": "sk-0b44b844cd3940daa77f6eb0089fff32"  # 请替换为你的实际密码和API密钥
}


def get_api_key():
    """从session中获取API密钥"""
    return session.get("api_key")


def verify_password(password):
    """验证密码并返回对应的API密钥"""
    return API_PASSWORD_MAP.get(password)


BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


# 验证API密钥
def verify_api_key(api_key):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "test"},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }
    try:
        response = requests.post(BASE_URL, headers=headers, json=data)
        return response.status_code == 200
    except Exception:
        return False


# 定义函数与模型交互
def ask_question(prompt, conversation_id=None):
    api_key = get_api_key()
    if not api_key:
        return "密钥错误，请重新复制"

    # 获取历史对话
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    if conversation_id and "conversations" in session:
        conversation = session["conversations"].get(conversation_id, {})
        conversation_messages = conversation.get("messages", [])
        # 只取最近的10条消息作为上下文
        for msg in conversation_messages[-10:]:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})

    # 添加当前问题
    messages.append({"role": "user", "content": prompt})

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "qwen-plus",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4000,
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=data)
        if response.status_code == 200:
            content = (
                response.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "无法获取回复")
            )
            return content
        elif response.status_code == 401:
            return "密钥错误，请重新复制"
        else:
            return "服务暂时不可用，请稍后再试"
    except Exception as e:
        print(f"API调用错误: {str(e)}")
        return "网络连接错误，请检查网络后重试"


def generate_title(messages):
    """生成对话标题"""
    api_key = get_api_key()
    if not api_key:
        return None

    # 确保messages是列表类型
    if not isinstance(messages, list):
        if isinstance(messages, dict) and "messages" in messages:
            messages = messages["messages"]
        else:
            return None

    # 提取最近的对话内容
    recent_messages = messages[-4:] if len(messages) >= 4 else messages
    conversation_text = "\n".join(
        [
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}"
            for msg in recent_messages
            if isinstance(msg, dict)
        ]
    )

    prompt = (
        "用5个字总结这段对话的主题（直接返回5个字，不要有任何标点符号和额外文字）：\n\n"
        + conversation_text
    )

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "qwen-plus",
        "messages": [
            {
                "role": "system",
                "content": "你是一个简洁的��题生成助手，只返回5个字的标题，不返回任何其他内容。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            title = (
                response.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            # 清理标题，只保留中文字符
            title = "".join(char for char in title if "\u4e00" <= char <= "\u9fff")
            return title[:5] if title else None
        return None
    except Exception as e:
        print(f"生成标题时出错: {str(e)}")
        return None


@app.route("/verify_api_key", methods=["POST"])
def verify_key():
    password = request.json.get("api_key")  # 用户输入的是密码
    if not password:
        return jsonify({"status": "error", "message": "请输入密码"}), 400

    # 验证密码并获取API密钥
    api_key = verify_password(password)
    if not api_key:
        return jsonify({"status": "error", "message": "密码错误"}), 401

    # 验证API密钥是否有效
    if verify_api_key(api_key):
        session["api_key"] = api_key  # 存储真实的API密钥
        return jsonify({"status": "success", "message": "密码验证成功"})
    else:
        return jsonify({"status": "error", "message": "API密钥无效"}), 401


# 路由设置
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        if not get_api_key():
            return jsonify({"response": "密码错误，请重新输入", "error": "未授权"}), 401

        user_input = request.json.get("user_input")
        conversation_id = request.json.get("conversation_id")
        is_new_conversation = request.json.get("is_new_conversation", False)
        previous_conversation_id = request.json.get("previous_conversation_id")

        if not user_input:
            return jsonify({"response": "请输入内容", "error": "输入为空"}), 400

        # 如果是新建对话，先处理之前对话的标题生成
        if is_new_conversation and previous_conversation_id:
            if (
                "conversations" in session
                and previous_conversation_id in session["conversations"]
            ):
                prev_messages = session["conversations"][previous_conversation_id][
                    "messages"
                ]
                if prev_messages:
                    new_title = generate_title(prev_messages)
                    if new_title:
                        session["conversations"][previous_conversation_id][
                            "title"
                        ] = new_title
                        session.modified = True

        # 获取AI回复
        response = ask_question(user_input, conversation_id)
        current_time = datetime.now().strftime("%H:%M")

        # 获取或创建会话历史
        if "conversations" not in session:
            session["conversations"] = {}

        conversations = session.get("conversations", {})
        if conversation_id not in conversations:
            conversations[conversation_id] = {
                "messages": [],
                "title": f"对话 {len(conversations) + 1}",
                "time": current_time,
            }

        # 更新会话记录
        if "messages" not in conversations[conversation_id]:
            conversations[conversation_id]["messages"] = []

        conversations[conversation_id]["messages"].extend(
            [
                {"role": "user", "content": user_input, "timestamp": current_time},
                {"role": "assistant", "content": response, "timestamp": current_time},
            ]
        )

        # 检查是否需要生成标题
        messages_count = len(conversations[conversation_id]["messages"])
        should_generate_title = (
            messages_count == 2  # 第一次对话后
            or messages_count % 20 == 0  # 每十轮对话后
        )

        new_title = None
        if should_generate_title:
            new_title = generate_title(conversations[conversation_id]["messages"])
            if new_title:
                conversations[conversation_id]["title"] = new_title
                conversations[conversation_id]["time"] = current_time

        session["conversations"] = conversations
        session.modified = True

        return jsonify(
            {
                "response": response,
                "timestamp": current_time,
                "conversation_id": conversation_id,
                "new_title": new_title,
            }
        )

    except Exception as e:
        print(f"处理请求时出错: {str(e)}")
        return jsonify({"response": "服务器处理请求时出错", "error": str(e)}), 500


@app.route("/conversations", methods=["GET"])
def get_conversations():
    return jsonify(session.get("conversations", {}))


@app.route("/conversation/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    try:
        if "conversations" in session:
            conversations = session.get("conversations", {})
            if conversation_id in conversations:
                del conversations[conversation_id]
                session["conversations"] = conversations
                session.modified = True
                return jsonify({"status": "success", "message": "对话已删除"})
        return jsonify(
            {"status": "success", "message": "对话已删除"}
        )  # 即使对话不存在也返回成功
    except Exception as e:
        print(f"删除对话时出错: {str(e)}")
        return jsonify({"status": "error", "message": "删除失败，请重试"}), 500


@app.route("/conversation/<conversation_id>/clear", methods=["POST"])
def clear_conversation(conversation_id):
    if "conversations" in session and conversation_id in session["conversations"]:
        session["conversations"][conversation_id] = []
        session.modified = True
        return jsonify({"status": "success", "message": "对话已清空"})
    return jsonify({"status": "error", "message": "对话不存在"}), 404


@app.route("/update_api_key", methods=["POST"])
def update_api_key():
    password = request.json.get("api_key")  # 用户输入的是密码
    if not password:
        return jsonify({"status": "error", "message": "请输入密码"}), 400

    # 验证密码并获取API密钥
    api_key = verify_password(password)
    if not api_key:
        return jsonify({"status": "error", "message": "密码错误"}), 401

    # 验证API密钥是否有效
    if verify_api_key(api_key):
        session["api_key"] = api_key  # 存储真实的API密钥
        return jsonify({"status": "success", "message": "密码验证成功"})
    else:
        return jsonify({"status": "error", "message": "API密钥无效"}), 401


def find_free_port(start_port=5000):
    """找到一个可用的端口"""
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No free ports available")


async def generate_conversation_title(messages):
    """使用AI生成对话标题"""
    api_key = get_api_key()
    if not api_key:
        return "新对话"

    # 提取对话内容用于总结
    conversation_text = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in messages]
    )

    # 构建提示
    prompt = f"请为以下对话生成一个简短的标题（不超过15个字）：\n\n{conversation_text}"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "qwen-plus",
        "messages": [
            {
                "role": "system",
                "content": "你是一个帮助总结对话标题的助手。请生成简短、准确的标题。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=data)
        if response.status_code == 200:
            title = (
                response.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "新对话")
            )
            # 确保标题不超过15个字
            return title[:15]
        else:
            return "新对话"
    except Exception as e:
        print(f"生成标题时出错: {str(e)}")
        return "新对话"


@app.route("/conversation/<conversation_id>/title", methods=["POST"])
async def update_conversation_title(conversation_id):
    """更新对话标题"""
    try:
        if "conversations" not in session:
            return jsonify({"status": "error", "message": "对话不存在"}), 404

        conversations = session.get("conversations", {})
        if conversation_id not in conversations:
            return jsonify({"status": "error", "message": "对话不存在"}), 404

        # 获取对话消息
        messages = conversations[conversation_id]
        if not messages:
            return jsonify({"status": "error", "message": "对话为空"}), 400

        # 生成新标题
        new_title = await generate_conversation_title(messages)

        # 更新标题
        conversations[conversation_id]["title"] = new_title
        session["conversations"] = conversations
        session.modified = True

        return jsonify({"status": "success", "title": new_title})
    except Exception as e:
        print(f"更新标题时出错: {str(e)}")
        return jsonify({"status": "error", "message": "更新标题失败"}), 500


@app.route("/generate_title", methods=["POST"])
def generate_title_route():
    """��成对话标题的路由"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400

        conversation_id = data.get("conversation_id")
        messages = data.get("messages")
        force_generate = data.get("force_generate", False)  # 新增参数，强制生成标题

        if not conversation_id or not messages:
            return jsonify({"error": "缺少必要参数"}), 400

        # 获取当前消息数量
        messages_count = len(messages)
        should_generate_title = (
            force_generate  # 强制生成（用于新建对话时）
            or messages_count == 2  # 第一次对话后
            or messages_count % 20 == 0  # 每十轮对话后
        )

        if not should_generate_title:
            return jsonify({"message": "不需要生成标题"}), 200

        # 生成标题
        title = generate_title(messages)
        if title:
            # 更新会话中的标题
            if (
                "conversations" in session
                and conversation_id in session["conversations"]
            ):
                session["conversations"][conversation_id]["title"] = title
                session.modified = True

            return jsonify({"title": title})
        else:
            return jsonify({"error": "生成标题失败"}), 500

    except Exception as e:
        print(f"生成标题时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    try:
        port = find_free_port(5000)
        print(f"Starting server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        exit(1)
