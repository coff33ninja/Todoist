const API_URL = 'http://localhost:5000'; // Define the API URL

let currentConversationState = null;

document.getElementById('startConversationBtn')?.addEventListener('click', async () => {
    const statementElement = document.getElementById('received-item-statement');
    if (!statementElement) return;
    const statement = statementElement.value.trim();

    if (!statement) return;

    try {
        const response = await fetch(`${API_URL}/api/received_item`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ statement })
        });
        const data = await response.json();

        const conversationResultElement = document.getElementById('conversation-result');
        if (data.error) {
            if (conversationResultElement) {
                conversationResultElement.className = 'error-result';
                conversationResultElement.textContent = data.error;
            }
            return;
        }

        // Show conversation area and hide result
        const conversationAreaElement = document.getElementById('conversation-area');
        if (conversationAreaElement) {
            conversationAreaElement.style.display = 'block';
        }
        if (conversationResultElement) {
            conversationResultElement.textContent = '';
        }

        // Display question
        const questionElement = document.getElementById('conversation-question');
        if (questionElement) {
            questionElement.textContent = data.next_question;
        }

        // Store conversation state
        currentConversationState = data.conversation_state;

        // Clear and focus answer input
        const answerElement = document.getElementById('conversation-answer');
        if (answerElement) {
            answerElement.value = '';
            answerElement.focus();
        }
    } catch (error) {
        if (conversationResultElement) {
            conversationResultElement.className = 'error-result';
            conversationResultElement.textContent = 'Error connecting to server';
        }
    }
});

document.getElementById('answerBtn')?.addEventListener('click', async () => {
    if (!currentConversationState) return;

    const answerElement = document.getElementById('conversation-answer');
    if (!answerElement) return;
    const answer = answerElement.value.trim();

    if (!answer) return;

    try {
        const response = await fetch(`${API_URL}/api/received_item/continue`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_state: currentConversationState, answer })
        });
        const data = await response.json();

        const conversationResultElement = document.getElementById('conversation-result');
        if (data.error) {
            if (conversationResultElement) {
                conversationResultElement.className = 'error-result';
                conversationResultElement.textContent = data.error;
            }
            return;
        }

        if (data.status === 'completed') {
            // Conversation is complete
            const conversationAreaElement = document.getElementById('conversation-area');
            if (conversationAreaElement) {
                conversationAreaElement.style.display = 'none';
            }
            if (conversationResultElement) {
                conversationResultElement.className = 'success-result';
                conversationResultElement.textContent = data.message;
            }

            // Reset the form
            const statementElement = document.getElementById('received-item-statement');
            if (statementElement) {
                statementElement.value = '';
            }
            currentConversationState = null;
        } else {
            // Continue conversation
            const questionElement = document.getElementById('conversation-question');
            if (questionElement) {
                questionElement.textContent = data.next_question;
            }
            currentConversationState = data.conversation_state;
            if (answerElement) {
                answerElement.value = '';
                answerElement.focus();
            }
        }
    } catch (error) {
        if (conversationResultElement) {
            conversationResultElement.className = 'error-result';
            conversationResultElement.textContent = 'Error connecting to server';
        }
    }
});

// Make example statements clickable
document.querySelectorAll('.example-statement').forEach(example => {
    example.addEventListener('click', () => {
        const statement = example.textContent.replace(/['"]/g, '');
        const statementElement = document.getElementById('received-item-statement');
        if (statementElement) {
            statementElement.value = statement;
        }
        document.getElementById('startConversationBtn')?.click();
    });
});

// Allow Enter key to submit answers
document.getElementById('conversation-answer')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('answerBtn')?.click();
    }
});

document.getElementById('received-item-statement')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('startConversationBtn')?.click();
    }
});

// Load categories for dropdown
async function loadCategories() {
    try {
        const response = await fetch(`${API_URL}/api/categories`);
        const data = await response.json();
        const select = document.getElementById('category');
        if (select) {
            data.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Load existing locations for autocomplete
async function loadLocations() {
    try {
        const response = await fetch(`${API_URL}/api/locations`);
        const data = await response.json();
        const datalist = document.getElementById('locations');
        if (datalist) {
            datalist.innerHTML = data.locations.map(location => `<option value="${location}">`).join('');
        }
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

// Call the load functions on page load
loadCategories();
loadLocations();
