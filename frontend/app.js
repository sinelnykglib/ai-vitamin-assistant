// Стан додатку
let sessionId = generateSessionId();
let conversationHistory = [];

// Генерація унікального ID сесії
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Додавання повідомлення в чат
function addMessage(role, content) {
    const chatArea = document.getElementById("chatArea");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;
    
    const messageContent = document.createElement("div");
    messageContent.className = "message-content";
    messageContent.innerHTML = content.replace(/\n/g, '<br>');
    
    const messageTime = document.createElement("div");
    messageTime.className = "message-time";
    messageTime.innerText = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageTime);
    chatArea.appendChild(messageDiv);
    
    // Скрол до нового повідомлення
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Оновлення графіку прийому
function updateSchedule(recommendations) {
    const schedulePanel = document.getElementById("schedulePanel");
    const morningList = document.getElementById("morningList");
    const dinnerList = document.getElementById("dinnerList");
    const eveningList = document.getElementById("eveningList");
    
    if (!recommendations || recommendations.length === 0) {
        schedulePanel.style.display = "none";
        return;
    }
    
    // Очищаємо списки
    morningList.innerHTML = "";
    dinnerList.innerHTML = "";
    eveningList.innerHTML = "";
    
    // Групуємо за часом
    recommendations.forEach(rec => {
        const li = document.createElement("li");
        let text = rec.vitamin;
        if (rec.dosage) text += ` (${rec.dosage})`;
        if (rec.notes) text += ` - ${rec.notes}`;
        li.textContent = text;
        
        switch(rec.time) {
            case "morning":
                morningList.appendChild(li);
                break;
            case "dinner":
                dinnerList.appendChild(li);
                break;
            case "evening":
                eveningList.appendChild(li);
                break;
        }
    });
    
    schedulePanel.style.display = "block";
}

// Показ індикатора завантаження
function showLoading() {
    const chatArea = document.getElementById("chatArea");
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "message assistant";
    loadingDiv.id = "loadingMessage";
    loadingDiv.innerHTML = `
        <div class="message-content">
            <div class="loading"></div> Думаю...
        </div>
    `;
    chatArea.appendChild(loadingDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Приховування індикатора завантаження
function hideLoading() {
    const loadingDiv = document.getElementById("loadingMessage");
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Основний функціонал відправки
async function send() {
    const msgInput = document.getElementById("msg");
    const message = msgInput.value.trim();
    
    if (!message) return;
    
    // Очищаємо поле вводу
    msgInput.value = "";
    
    // Додаємо повідомлення користувача в чат
    addMessage("user", message);
    
    // Додаємо в історію розмови
    conversationHistory.push({
        role: "user",
        content: message,
        timestamp: new Date().toISOString()
    });
    
    // Показуємо індикатор завантаження
    showLoading();
    
    try {
        // Отримуємо профіль користувача з localStorage (можна розширити)
        const userProfile = getUserProfile();
        
        const response = await fetch("http://localhost:8000/recommend", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: "user1",
                session_id: sessionId,
                message: message,
                conversation_history: conversationHistory,
                user_profile: userProfile,
                platform: "web",
                language: "uk",
                timestamp: new Date().toISOString()
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Приховуємо індикатор завантаження
        hideLoading();
        
        // Додаємо відповідь асистента в чат
        addMessage("assistant", data.reply_message);
        
        // Додаємо в історію розмови
        conversationHistory.push({
            role: "assistant",
            content: data.reply_message,
            timestamp: new Date().toISOString()
        });
        
        // Оновлюємо графік прийому
        if (data.recommendations && data.recommendations.length > 0) {
            updateSchedule(data.recommendations);
        }
        
        // Логування для дебагінгу
        console.log("Response:", data);
        console.log("Processing time:", data.processing_time_ms, "ms");
        console.log("Confidence:", data.confidence_score);
        
    } catch (error) {
        console.error("Error:", error);
        hideLoading();
        addMessage("assistant", "❌ Вибачте, сталася помилка. Спробуйте ще раз.");
        
        // Показуємо деталі помилки в консолі
        console.error("Error details:", error);
    }
}

// Отримання профілю користувача (можна розширити формою)
function getUserProfile() {
    // Тут можна додати форму для заповнення профілю
    // Поки що повертаємо тестові дані
    const savedProfile = localStorage.getItem("userProfile");
    if (savedProfile) {
        return JSON.parse(savedProfile);
    }
    
    // Дефолтний профіль
    return {
        age: null,
        gender: null,
        allergies: [],
        current_supplements: [],
        health_goals: []
    };
}

// Збереження профілю користувача (для майбутнього розширення)
function saveUserProfile(profile) {
    localStorage.setItem("userProfile", JSON.stringify(profile));
}

// Функція для очищення історії
function clearHistory() {
    sessionId = generateSessionId();
    conversationHistory = [];
    const chatArea = document.getElementById("chatArea");
    chatArea.innerHTML = `
        <div class="message assistant">
            <div class="message-content">
                👋 Вітаю! Я ваш віртуальний асистент з прийому вітамінів. 
                Запитайте мене, які вітаміни вам приймати, і я складу персональний графік!
            </div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        </div>
    `;
    document.getElementById("schedulePanel").style.display = "none";
}