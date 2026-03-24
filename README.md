# ai-vitamin-assistant
An AI-powered workflow that analyzes user input and provides personalized vitamin intake recommendations.

🧠 AI Vitamin Intake Assistant

An AI-powered automation workflow that processes user input and generates structured vitamin intake recommendations using a local or API-based LLM.

Built with n8n for orchestration and designed as a modular, extensible pipeline.

🚀 Overview

This project automates the process of recommending when and how to take vitamins based on natural language input from users.

Instead of relying on raw AI responses, the system uses a structured pipeline:

Extracts key data from user input
Processes it through an AI model
Validates and formats the output
Returns clean, actionable recommendations
⚙️ Architecture
User Input (Telegram / Web / API)
        ↓
Webhook (n8n)
        ↓
AI Parsing (extract structured data)
        ↓
AI Recommendation Engine
        ↓
Post-processing (formatting + validation)
        ↓
Response to user
🧩 Features
✅ Natural language input (e.g. "I take magnesium and vitamin D")
✅ Structured data extraction using AI
✅ Personalized vitamin intake recommendations
✅ Clean and formatted output (not raw AI text)
✅ Modular workflow (easy to extend)
✅ Supports both local and API-based LLMs
🛠 Tech Stack
Workflow automation: n8n
AI / LLM:
Local: Ollama (optional)
Cloud: OpenAI API (optional)
Interface (optional):
Telegram Bot / Webhook / REST API
🧠 How It Works
1. Input

User sends a message:

"I take magnesium and vitamin D"
2. AI Parsing

The system extracts structured data:

{
  "vitamins": ["magnesium", "vitamin D"],
  "goal": "optimize intake timing"
}
3. AI Recommendation

The AI generates structured output:

[
  {
    "vitamin": "Magnesium",
    "time": "evening",
    "food": "with food",
    "notes": "supports relaxation"
  },
  {
    "vitamin": "Vitamin D",
    "time": "morning",
    "food": "with food",
    "notes": "fat-soluble vitamin"
  }
]
4. Output

Formatted response:

🕗 Morning:
- Vitamin D (with food)

🌙 Evening:
- Magnesium (with food)
▶️ Getting Started
1. Clone the repository
git clone https://github.com/your-username/ai-vitamin-assistant.git
cd ai-vitamin-assistant
2. Setup n8n

Install and run n8n:

npm install -g n8n
n8n

or via Docker:

docker run -it --rm \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
3. Configure AI
Option A: Local (recommended for privacy)

Install Ollama:

ollama run llama3
Option B: Cloud

Use OpenAI API key in n8n credentials.

4. Import Workflow
Open n8n UI: http://localhost:5678
Import the provided workflow JSON
Configure credentials
Run the workflow
⚠️ Disclaimer

This project provides general wellness guidance only and is not medical advice.
Always consult a healthcare professional before making decisions about supplements.

🧱 Future Improvements
🔄 User memory (track ongoing vitamin usage)
🧪 Rule-based validation layer (hybrid AI + logic)
📱 Mobile app integration
📊 Analytics dashboard
🔔 Smart reminders
🤝 Contributing

Feel free to open issues or submit pull requests.

📄 License

MIT License
