# ChatMe! - 现代化的AI聊天应用

一个基于OpenAI API的现代化聊天应用，具有优雅的UI设计和流畅的用户体验。

## 功能特点

- 🎨 优雅的深色/浅色主题切换
- 💬 流畅的打字机效果
- 📝 Markdown格式支持
- 🔄 自动生成对话标题
- 📱 响应式设计
- 🔒 安全的API密钥管理
- 🎯 实时API状态指示
- 💾 本地对话历史保存
- ⚡ 异步消息处理
- 🌈 丰富的动画效果

## 技术栈

- 后端：Flask + Python
- 前端：HTML5 + CSS3 + JavaScript
- API：OpenAI GPT API
- 样式：Tailwind CSS
- 部署：Gunicorn + Nginx

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/chatme.git
cd chatme
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 设置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，添加你的OpenAI API密钥
```

5. 运行应用：
```bash
python app.py
```

访问 http://localhost:5000 即可使用应用。

## 部署说明

### 使用Gunicorn部署

1. 安装Gunicorn：
```bash
pip install gunicorn
```

2. 运行应用：
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 环境变量

- `OPENAI_API_KEY`: OpenAI API密钥
- `SECRET_KEY`: Flask会话密钥
- `DEBUG`: 调试模式开关（生产环境设为False）
- `PORT`: 应用运行端口（默认5000）

## 开发说明

### 项目结构

```
chatme/
├── config/              # 配置文件
│   ├── __init__.py
│   └── settings.py
├── static/             # 静态资源
│   ├── css/
│   ├── js/
│   └── images/
├── templates/          # HTML模板
├── utils/             # 工具函数
│   ├── __init__.py
│   ├── auth.py
│   └── chat.py
├── app.py            # 主应用文件
├── requirements.txt  # 依赖管理
└── README.md        # 项目说明
```

### 代码风格

- 遵循PEP 8规范
- 使用类型注解
- 保持代码简洁清晰
- 添加适当的注释

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情

## 作者

陈铭凯 - [个人网站](https://your-website.com)

## 致谢

- OpenAI团队提供的强大API
- Flask框架的简洁优雅
- 所有贡献者的支持 