from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import asyncio
import os
from config.settings import *
from utils.auth import require_api_key, validate_api_key
from utils.chat import chat_manager

app = Flask(__name__)
CORS(app)
app.secret_key = SECRET_KEY
app.config["JSON_AS_ASCII"] = False


# 路由：主页
@app.route("/")
def index():
    return render_template("index.html")


# 路由：更新API密钥
@app.route("/update_api_key", methods=["POST"])
def update_api_key():
    try:
        data = request.get_json()
        api_key = data.get("api_key")

        if not api_key:
            return jsonify({"error": "未提供API密钥"}), 400

        if not validate_api_key(api_key):
            return jsonify({"error": "API密钥无效"}), 400

        session["api_key"] = api_key
        return jsonify({"message": "密钥更新成功"})

    except Exception as e:
        print(f"更新API密钥错误: {str(e)}")
        return jsonify({"error": "更新失败"}), 500


# 路由：发送消息
@app.route("/ask", methods=["POST"])
@require_api_key
def ask():
    try:
        data = request.get_json()
        user_input = data.get("user_input")
        conversation_id = data.get("conversation_id")
        is_new_conversation = data.get("is_new_conversation", False)

        if not user_input:
            return jsonify({"error": "消息不能为空"}), 400

        # 创建新对话或获取现有对话
        if is_new_conversation or not conversation_id:
            conversation_id = chat_manager.create_conversation()

        # 添加用户消息
        chat_manager.add_message(conversation_id, "user", user_input)

        # 获取AI响应
        response = asyncio.run(
            chat_manager.generate_response(conversation_id, user_input)
        )

        # 处理流式响应
        full_response = ""
        async for chunk in response:
            if chunk and chunk.choices and chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content

        # 添加AI响应到对话
        chat_manager.add_message(conversation_id, "assistant", full_response)

        return jsonify({"response": full_response, "conversation_id": conversation_id})

    except Exception as e:
        print(f"处理消息错误: {str(e)}")
        return jsonify({"error": "处理失败"}), 500


# 路由：生成标题
@app.route("/generate_title", methods=["POST"])
@require_api_key
def generate_title():
    try:
        data = request.get_json()
        conversation_id = data.get("conversation_id")
        force_generate = data.get("force_generate", False)

        if not conversation_id:
            return jsonify({"error": "未提供对话ID"}), 400

        # 获取对话
        conversation = chat_manager.get_conversation(conversation_id)
        if not conversation:
            return jsonify({"error": "对话不存在"}), 404

        # 如果已有标题且不强制生成，直接返回
        if conversation.get("title") and not force_generate:
            return jsonify({"title": conversation["title"]})

        # 生成新标题
        title = asyncio.run(chat_manager.generate_title(conversation_id))
        if not title:
            return jsonify({"error": "生成标题失败"}), 500

        return jsonify({"title": title})

    except Exception as e:
        print(f"生成标题错误: {str(e)}")
        return jsonify({"error": "生成失败"}), 500


# 路由：获取所有对话
@app.route("/conversations", methods=["GET"])
def get_conversations():
    try:
        return jsonify(chat_manager.conversations)
    except Exception as e:
        print(f"获取对话列表错误: {str(e)}")
        return jsonify({"error": "获取失败"}), 500


# 路由：删除对话
@app.route("/conversation/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    try:
        if chat_manager.delete_conversation(conversation_id):
            return jsonify({"message": "删除成功"})
        return jsonify({"error": "对话不存在"}), 404
    except Exception as e:
        print(f"删除对话错误: {str(e)}")
        return jsonify({"error": "删除失败"}), 500


# 路由：清空对话
@app.route("/conversation/<conversation_id>/clear", methods=["POST"])
def clear_conversation(conversation_id):
    try:
        if chat_manager.clear_conversation(conversation_id):
            return jsonify({"message": "清空成功"})
        return jsonify({"error": "对话不存在"}), 404
    except Exception as e:
        print(f"清空对话错误: {str(e)}")
        return jsonify({"error": "清空失败"}), 500


if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)
