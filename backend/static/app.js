// backend/static/app.js
document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const roleRadios = document.querySelectorAll('input[name="role"]');
    const seedDbButton = document.getElementById('seed-db-button');
    const statusMessage = document.getElementById('status-message');

    let currentRole = 'patient';
    let sessionId = null;

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'agent-message');
        
        messageDiv.innerHTML = text.replace(/\n/g, '<br>');

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; 
    }

    async function sendMessage() {
        const prompt = userInput.value.trim();
        if (prompt === '') return;

        addMessage(prompt, 'user');
        userInput.value = '';

        try {
            statusMessage.textContent = 'Agent is thinking...';
            statusMessage.classList.remove('error-message');
            
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    prompt: prompt, 
                    role: currentRole, 
                    session_id: sessionId 
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Server returned an error.');
            }

            const data = await response.json();
            
            sessionId = data.session_id;

            addMessage(data.response, 'agent');
            statusMessage.textContent = '';
        } catch (error) {
            console.error('Error:', error);
            const errorMessage = `Error: ${error.message}`;
            addMessage(errorMessage, 'agent');
            statusMessage.textContent = errorMessage;
            statusMessage.classList.add('error-message');
        }
    }

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    roleRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            currentRole = e.target.value;
            sessionId = null; 
            statusMessage.textContent = `Switched to ${currentRole} role. New conversation started.`;
            chatMessages.innerHTML = `<div class="message system-message">Role switched to ${currentRole}. How can I assist you?</div>`;
        });
    });

    seedDbButton.addEventListener('click', async () => {
        statusMessage.textContent = 'Seeding database... This may take a moment.';
        statusMessage.classList.remove('error-message');
        try {
            const response = await fetch('/seed', { method: 'GET' });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to seed database.');
            }
            const data = await response.json();
            statusMessage.textContent = data.message;
        } catch (error) {
            console.error('Error seeding database:', error);
            statusMessage.textContent = `Error: ${error.message}`;
            statusMessage.classList.add('error-message');
        }
    });
});