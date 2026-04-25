const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const themeToggle = document.getElementById('theme-toggle');
const languageSelect = document.getElementById('language-select');
const suggestionsContainer = document.getElementById('suggestions');

// Generate a random session ID for this visit
const sessionId = Math.random().toString(36).substring(2, 15);

// Theme Toggle Logic
themeToggle.addEventListener('click', () => {
    const currentTheme = document.body.getAttribute('data-theme');
    if (currentTheme === 'dark') {
        document.body.removeAttribute('data-theme');
        themeToggle.textContent = '🌙';
    } else {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️';
    }
});

function appendMessage(sender, text) {
    const isBot = sender === 'AI';
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isBot ? 'bot-message' : 'user-message'} fade-in`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = sender === 'AI' ? 'AI' : 'U';

    const content = document.createElement('div');
    content.className = 'content';
    content.innerHTML = `<p>${text}</p>`;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatBox.appendChild(messageDiv);
    
    // Auto-scroll
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message bot-message fade-in typing-indicator-wrapper';
    indicator.id = 'typing-indicator';
    
    indicator.innerHTML = `
        <div class="avatar">AI</div>
        <div class="typing-indicator">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    chatBox.appendChild(indicator);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function updateSuggestions(suggestions) {
    suggestionsContainer.innerHTML = '';
    suggestions.forEach(sug => {
        const btn = document.createElement('button');
        btn.className = 'suggestion-btn fade-in';
        btn.textContent = sug;
        btn.onclick = () => sendSuggestion(sug);
        suggestionsContainer.appendChild(btn);
    });
}

async function sendMessage(text) {
    if (!text.trim()) return;

    // Clear suggestions
    suggestionsContainer.innerHTML = '';

    appendMessage('User', text);
    userInput.value = '';
    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: text,
                language: languageSelect.value
            })
        });

        const data = await response.json();
        removeTypingIndicator();
        appendMessage('AI', data.response);
        
        if (data.suggested_actions && data.suggested_actions.length > 0) {
            updateSuggestions(data.suggested_actions);
        }
    } catch (error) {
        console.error("Error:", error);
        removeTypingIndicator();
        appendMessage('AI', 'Sorry, I am having trouble connecting to the network.');
    }
}

// Attach to suggestion buttons
window.sendSuggestion = function(text) {
    sendMessage(text);
};

sendBtn.addEventListener('click', () => sendMessage(userInput.value));
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage(userInput.value);
});
