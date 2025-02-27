# 🧠 AI-Powered Task Manager for the Angry Wife™

Ever had that moment when your significant other asks "Where did you put that thing?" and you have no idea what "that thing" is? Welcome to the solution! This project combines the power of natural language processing, inventory management, and AI to create the ultimate household organization system.

## 🌟 Features

- **Natural Language Queries**: Just ask normally! "Where's that thing I bought last week?" - it understands!
- **Smart Inventory Management**: Track items, their locations, and history
- **Receipt Processing**: Scan receipts to automatically add items
- **Budget Tracking**: Keep track of spending (before someone else does!)
- **Repair Management**: Track item repairs and maintenance
- **Trade History**: Keep records of items traded or gifted

## 🛠️ Setup

### Prerequisites

- **Python 3.11.x**: [Download Python](https://www.python.org/downloads/)
- **Git**: [Download Git](https://git-scm.com/downloads)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/coff33ninja/Todoist.git
   cd Todoist
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```bash
   python main.py
   ```

## 🚀 Usage

### Starting the Application
- Run `python main.py` to start the Flask server
- Alternatively, use `./start.bat start` (Windows) to launch
  - **Note**: `start.bat` handles most of the heavy lifting, including environment setup, starting the application, training models, running tests, and adding sample data. It provides an interactive menu for easy management.
- Access the API at `http://localhost:5000`

---

## 🌱 Personal Note

I'm diving into AI like a toddler into a ball pit—enthusiastic but slightly confused. Python still laughs at my feeble attempts, and Node.js is actively plotting my demise. But this project must rise from the ashes of my GitHub graveyard, where half-baked ideas, abandoned dreams, and forgotten commits go to rest.

Why? Because my wife got sick of me asking the same dumb questions over and over. OpenAI also had a hand in this after a brief but life-altering chat in conversation.txt. So, here’s to finally finishing a project—may it not join its fallen brothers in the land of unfinished code! 🚀💀

---

### API Endpoints

#### Items Management
- `GET /api/items` - List all items
- `POST /api/items` - Add new item
- `GET /api/search?q=query` - Search items

#### Natural Language Interface
- `POST /api/query`
  ```json
  {
    "query": "Where did I put my keys?"
  }
  ```

#### Repair Tracking
- `POST /api/repairs` - Log new repairs
- `GET /api/repairs` - View repair history
- `POST /api/components` - Track repair parts

#### Budget Management
- `POST /api/budget` - Set budget
- `GET /api/budget` - View financial status

#### Receipt Processing
- `POST /api/receipts/upload` - Upload and process receipt
- `GET /api/receipts/[filename]` - View processed receipts

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

### Example Queries

```python
# Natural language queries the system understands:
"Show me all items in the garage"
"What did I buy last month?"
"How much have I spent on electronics?"
"Where are my winter clothes?"
"List all items that need repair"
```

## ⚙️ AI Configurations

This project allows for various configurations to enhance user experience and AI interaction:

- **User Preferences**: Set preferences for notifications, item categories, and more.
- **Frequently Asked Questions**: AI can remember and prioritize common queries.
- **Common Item Locations**: Learns and suggests typical storage locations for items.
- **Notification Settings**: Configure how and when you receive alerts about inventory changes or budget updates.

## 🤖 AI Integration

This project is designed to work with various AI models to enhance its capabilities:

1. **Natural Language Understanding**: Uses pattern matching and AI to understand complex queries
2. **Receipt OCR**: Automatically extracts information from receipts
3. **Smart Categorization**: AI-powered item categorization
4. **Location Memory**: Learns common item locations
5. **Predictive Maintenance**: Suggests when items might need maintenance

## 🎯 Use Cases

1. **The "Where Is It?" Scenario**
   - Wife: "Where's that thing I bought at the store last week?"
   - You: *quickly queries system* "The blue vase is in the living room cabinet!"
   - Result: Domestic tranquility maintained ✌️

2. **The Budget Discussion**
   - Wife: "How much did you spend on gaming stuff this month?"
   - You: *checks budget tracker* "Actually, I'm under budget by $50!"
   - Result: Data-driven victory 📊

3. **The Receipt Savior**
   - Wife: "Where's the receipt for the blender? It's broken!"
   - You: *pulls up warranty info and receipt in seconds*
   - Result: Customer service hero 🧨‍♂️

## Current Implementation Status

### Implemented Features
- Basic inventory management
- Repair tracking
- Budget management
- Receipt processing
- API endpoints for core functionality

### Missing Features
- Advanced NLP for natural queries
- Sophisticated OCR for receipts
- AI model integration
- Context-aware conversations
- Financial insights and forecasting

## Next Steps

1. Enhance `nlu_processor.py` with ML models
2. Improve `ocr_processor.py` with advanced preprocessing
3. Add AI model training scripts
4. Expand API endpoints for new features
5. Update documentation and tests

## 🤝 Contributing

Feel free to contribute! We're especially looking for:
- More natural language patterns
- AI model integrations
- Additional features for domestic peace

## 📝 License

MIT License - Feel free to use this to save your own domestic situations!

## 🙏 Acknowledgments

- Thanks to all the spouses who inspired this project
- Special thanks to the AI models that help us remember things
- Dedicated to everyone who's ever been asked "Where did you put it?"

## 🚨 Disclaimer

This project does not guarantee:
- That you'll never lose things again
- That you'll remember everything
- Complete domestic harmony

But it sure helps! 😉

---
Remember: An organized home is a happy home! 🏠✨