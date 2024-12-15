// 全局变量
let isSending = false;
let conversations = {};
let currentConversationId = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    if (checkFunctionality()) {
        initializeWithRetry();
        scrollToBottom();
        initializeEventListeners();
    }
});

// 初始化事件监听器
function initializeEventListeners() {
    // 输入框事件
    const userInput = document.getElementById('userInput');
    userInput.addEventListener('input', () => autoResizeTextarea(userInput));
    userInput.addEventListener('keydown', handleInputKeydown);

    // 标题容器3D效果
    const titleContainer = document.getElementById('titleContainer');
    const title = document.getElementById('title');
    titleContainer.addEventListener('mousemove', handleTitleHover);
    titleContainer.addEventListener('mouseleave', handleTitleLeave);
    titleContainer.addEventListener('click', handleTitleClick);

    // 消息点击复制
    document.querySelectorAll('.message-content').forEach(message => {
        message.addEventListener('click', () => {
            copyToClipboard(message.textContent, message);
        });
    });
}

// API相关函数
async function updateApiKey() {
    const apiKey = document.getElementById('apiKeyInput').value;
    if (!apiKey) {
        showApiKeyMessage('error', '请输入密码');
        return;
    }

    const modalContent = document.querySelector('.modal-content');
    const saveBtn = document.querySelector('.save-btn');
    const apiKeyInput = document.getElementById('apiKeyInput');

    try {
        modalContent.classList.add('verifying');
        saveBtn.classList.add('verifying');
        apiKeyInput.classList.add('verifying');
        saveBtn.disabled = true;

        const response = await fetch('/update_api_key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess();
            setTimeout(() => {
                hideApiKeyModal();
                apiKeyInput.value = '';
            }, 1000);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('网络错误，请重试');
    } finally {
        modalContent.classList.remove('verifying');
        saveBtn.classList.remove('verifying');
        apiKeyInput.classList.remove('verifying');
        saveBtn.disabled = false;
    }
}

// 对话管理函数
async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    if (!message || isSending) return;

    const apiStatus = document.querySelector('.api-status');
    apiStatus.classList.add('show');
    isSending = true;

    try {
        const isNewConversation = !currentConversationId;
        const previousId = isNewConversation ? null : currentConversationId;

        if (isNewConversation) {
            await createNewConversation();
        }

        userInput.disabled = true;
        const timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

        // 添加用户消息到UI
        const chatContainer = document.getElementById('chatContainer');
        const userMessageDiv = createMessageElement(message, true, timestamp);
        const assistantMessageDiv = createMessageElement(createLoadingDots(), false, timestamp);

        chatContainer.appendChild(userMessageDiv);
        chatContainer.appendChild(assistantMessageDiv);
        scrollToBottom();

        // 发送请求
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: message,
                conversation_id: currentConversationId,
                is_new_conversation: isNewConversation,
                previous_conversation_id: previousId
            })
        });

        if (!response.ok) {
            if (response.status === 401) {
                chatContainer.removeChild(assistantMessageDiv);
                showApiKeyModal();
                return;
            }
            throw new Error('请求失败');
        }

        const data = await response.json();

        // 更新对话内容
        if (!conversations[currentConversationId]) {
            conversations[currentConversationId] = {
                id: currentConversationId,
                title: `对话 ${Object.keys(conversations).length + 1}`,
                time: new Date().toLocaleString(),
                messages: []
            };
        }

        conversations[currentConversationId].messages.push(
            { role: 'user', content: message, timestamp },
            { role: 'assistant', content: data.response, timestamp }
        );

        // 更新UI显示AI回复
        const contentDiv = assistantMessageDiv.querySelector('.message-content');
        await typeWriter(contentDiv, data.response);

        // 检查是否需要生成标题
        const messagesCount = conversations[currentConversationId].messages.length;
        if (messagesCount === 2 || messagesCount % 20 === 0) {
            await generateTitle(currentConversationId);
        }

        // 保存状态
        localStorage.setItem('conversations', JSON.stringify(conversations));
        updateConversationList();

        // 清理输入框
        userInput.value = '';
        userInput.style.height = '36px';

    } catch (error) {
        console.error('发送消息失败:', error);
        showToast(error.message, 'error');
    } finally {
        apiStatus.classList.remove('show');
        isSending = false;
        userInput.disabled = false;
        userInput.focus();
    }
}

// UI辅助函数
function scrollToBottom() {
    const container = document.getElementById('chatContainer');
    container.scrollTop = container.scrollHeight;
}

function createLoadingDots() {
    return `<div class="loading-dots">
        <span></span><span></span><span></span>
    </div>`;
}

async function typeWriter(element, text, speed = 30) {
    return new Promise((resolve) => {
        if (text.includes('```') || text.includes('`') || text.includes('*')) {
            element.innerHTML = marked.parse(text);
            showTimestamp(element);
            resolve();
        } else {
            let i = 0;
            element.innerHTML = '';
            const formattedText = formatText(text);

            function type() {
                if (i < formattedText.length) {
                    element.innerHTML = formattedText.slice(0, i + 1);
                    i++;
                    setTimeout(type, speed);
                } else {
                    showTimestamp(element);
                    resolve();
                }
            }
            type();
        }
    });
}

// 工具函数
function formatText(text) {
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

function showTimestamp(element) {
    const timestamp = element.parentElement.querySelector('.message-timestamp');
    if (timestamp) {
        setTimeout(() => timestamp.classList.add('show'), 200);
    }
}

// 错误处理
window.onerror = function (msg, url, lineNo, columnNo, error) {
    console.error('Error:', { msg, url, lineNo, columnNo, error });
    showToast('发生错误，正在尝试恢复...', 'error');
    return false;
};

// 主题切换
const themeToggle = document.getElementById('themeToggle');
const themeMode = document.getElementById('themeMode');

function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    themeToggle.checked = theme === 'light';
}

function updateTheme() {
    const mode = themeMode.value;
    const theme = mode === 'auto' ? getSystemTheme() : mode;
    applyTheme(theme);
    localStorage.setItem('themeMode', mode);
}

// 初始化主题
const savedThemeMode = localStorage.getItem('themeMode') || 'auto';
themeMode.value = savedThemeMode;
updateTheme();

// 监听系统主题变化
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (themeMode.value === 'auto') {
        updateTheme();
    }
});

// 监听主题切换
themeMode.addEventListener('change', updateTheme);
themeToggle.addEventListener('change', function () {
    themeMode.value = this.checked ? 'light' : 'dark';
    updateTheme();
}); 