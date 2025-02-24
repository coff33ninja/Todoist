# 🧠 AI-Powered Task Manager for the Angry Wife™

Ever had that moment when your significant other asks "Where did you put that thing?" and you have no idea what "that thing" is? Welcome to the solution! This project combines the power of natural language processing, inventory management, and AI to create the ultimate household organization system.

## 🌟 Features

- **Natural Language Queries**: Just ask normally! "Where's that thing I bought last week?" - it understands!
- **Smart Inventory Management**: Track items, their locations, and history
- **Receipt Processing**: Scan receipts to automatically add items
- **Budget Tracking**: Keep track of spending (before someone else does!)
- **Repair Management**: Track item repairs and maintenance
- **Trade History**: Keep record of items traded or gifted

## 🛠️ Setup

### Prerequisites

```bash
# Required Python version
Python 3.8 or higher

# Required packages
pip install -r requirements.txt
```

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Todoist.git
cd Todoist
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python main.py
```

## 🚀 Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://localhost:5000`

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

#### Receipt Processing
- `POST /api/receipts/upload` - Upload and process receipt

#### Budget Management
- `GET /api/budget` - Get budget status
- `POST /api/budget` - Update budget

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
   - Result: Customer service hero 🦸‍♂️

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
Remember: A organized home is a happy home! 🏠✨