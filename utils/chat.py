import openai
from datetime import datetime
from config.settings import OPENAI_MODEL
from utils.auth import get_api_key


class ChatManager:
    def __init__(self):
        self.conversations = {}

    def create_conversation(self):
        """创建新对话"""
        conversation_id = str(datetime.now().timestamp())
        self.conversations[conversation_id] = {
            "messages": [],
            "title": None,
            "created_at": datetime.now().isoformat(),
        }
        return conversation_id

    def add_message(self, conversation_id, role, content):
        """添加消息到对话"""
        if conversation_id not in self.conversations:
            conversation_id = self.create_conversation()

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
        self.conversations[conversation_id]["messages"].append(message)
        return message

    async def generate_response(self, conversation_id, user_input):
        """生成AI响应"""
        try:
            openai.api_key = get_api_key()

            # 获取对话历史
            messages = []
            if conversation_id in self.conversations:
                for msg in self.conversations[conversation_id]["messages"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

            # 添加用户输入
            messages.append({"role": "user", "content": user_input})

            # 调用API获取响应
            response = await openai.ChatCompletion.acreate(
                model=OPENAI_MODEL, messages=messages, temperature=0.7, stream=True
            )

            return response

        except Exception as e:
            print(f"生成响应错误: {str(e)}")
            raise

    async def generate_title(self, conversation_id):
        """生成对话标题"""
        try:
            if conversation_id not in self.conversations:
                return None

            messages = self.conversations[conversation_id]["messages"]
            if not messages:
                return None

            # 构建标题生成提示
            context = "\n".join([f"{m['role']}: {m['content']}" for m in messages[:2]])
            prompt = f"请为以下对话生成一个简短的中文标题（不超过15个字）：\n{context}"

            openai.api_key = get_api_key()
            response = await openai.ChatCompletion.acreate(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=30,
            )

            title = response.choices[0].message.content.strip()
            self.conversations[conversation_id]["title"] = title
            return title

        except Exception as e:
            print(f"生成标题错误: {str(e)}")
            return None

    def get_conversation(self, conversation_id):
        """获取对话内容"""
        return self.conversations.get(conversation_id)

    def delete_conversation(self, conversation_id):
        """删除对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    def clear_conversation(self, conversation_id):
        """清空对话"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["messages"] = []
            return True
        return False


# 创建全局聊天管理器实例
chat_manager = ChatManager()
