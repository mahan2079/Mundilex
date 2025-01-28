# MundiLex - Your AI-Powered Language Immersion Companion 🌍📚

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-Yes-green.svg)](https://github.com/yourusername/MundiLex/graphs/commit-activity)

**Never lose immersion again!** MundiLex is your personal language learning sidekick that helps you understand foreign media content instantly through magical clipboard monitoring ✨

![MundiLex Demo](https://via.placeholder.com/800x400.png?text=MundiLex+Demo+GIF+-+Clipboard+Monitoring+%26+Flashcards)

**Developer:** Mahan Dashti Gohari ([@Mahan2079](mailto:mahan.dashti.gohari@gmail.com))

## 🚀 Features That Make Language Learning Magical

### 🌟 Core Magic
- **AI-Powered Instant Definitions** (Powered by Groq/Llama3-70B)
- **Real-Time Clipboard Monitoring** 👀  
  (Watch movies/read articles → copy words → instant understanding!)
- **Native Language Explanations**  
  (Learn in your target language _or_ get translations when needed)
- **Multi-Language Support**: German, English, French, Italian, Spanish, Russian

### 🧠 Learning Superpowers
- 📌 Save words as interactive flashcards
- 💖 Favorite important vocabulary
- 🔊 Text-to-Speech pronunciation
- 📥 Import/Export your learning progress
- 🔄 Flip flashcards for spaced repetition

### 🎨 Designed for Focus
- Dark mode UI with clean interface
- Non-intrusive desktop notifications
- Smart word validation (no API keys or long text)
- One-click save & organize

## ⚡ Quick Start

### Prerequisites
- Python 3.9+
- [Groq API Key](https://console.groq.com/keys) (Free account available)

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/MundiLex.git

# Navigate to project directory
cd MundiLex

# Install dependencies
pip install -r requirements.txt

# Set up your Groq API key (one-time setup)
echo "export GROQ_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

## 🎮 Usage - Learn Like Never Before

### Basic Flow
1. **Watch/Read Content** 🎥📖  
   Keep MundiLex running in the background
2. **Copy Unknown Words** ⎘  
   (Ctrl+C / Cmd+C like normal)
3. **Magic Happens** ✨  
   Get instant:
   - Desktop notifications
   - Detailed definitions
   - Native language examples
4. **Save & Review** 📚  
   Add to flashcards with one click

### Keyboard Shortcuts
| Action                | Shortcut          |
|-----------------------|-------------------|
| Toggle Clipboard Mode | Ctrl+Shift+M      |
| Quick Search          | Ctrl+Shift+S      |
| Save Current Word     | Ctrl+Shift+Enter  |

## 🛠️ Configuration

Customize in-app through the intuitive UI:
```python
# Available languages
SUPPORTED_LANGUAGES = [
    "German", "English", "French",
    "Italian", "Spanish", "Russian"
]

# Notification preferences
NOTIFICATION_SETTINGS = {
    "timeout": 10,      # Seconds
    "max_length": 256   # Characters
}
```

## 🌈 Why MundiLex?

Traditional Approach               | MundiLex Magic
-----------------------------------|-------------------
❌ Breaks immersion                | ✅ Seamless learning flow
❌ Manual lookups                  | ✅ Automatic detection
❌ Generic definitions             | ✅ AI-powered context
❌ Separate learning tools         | ✅ Integrated ecosystem

## 🤝 Contributing

We love contributors! Here's how to help:
1. 🐛 Report bugs [here](https://github.com/yourusername/MundiLex/issues)
2. 💡 Suggest new features
3. 🌍 Help with translations
4. 📚 Improve documentation

   
## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

## 🚨 Important Notes

- The current API key in code is **placeholder only**
- Always use your own Groq API key
- Data is stored locally in `vocab_data.json`

## 📬 Connect

**Developer:** Mahan Dashti Gohari  
📧 [mahan.dashti.gohari@gmail.com](mailto:mahan.dashti.gohari@gmail.com)  
💼 [LinkedIn Profile](www.linkedin.com/in/mahan-dashti-gohari-601b812b5)

**Happy Immersive Learning!** 🎉🌍
