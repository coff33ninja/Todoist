import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.nlu_processor import NLUProcessor
from datasets import Dataset

def main():
    # Sample training data
    X = [
        "show me all items in the kitchen",
        "how many items do I have in the garage",
        "what is the total value of my inventory",
        "list items that cost more than 50 dollars",
        "count all products in storage",
        "what items are in the living room",
        "how much are my things worth",
        "show me things that cost less than 20",
        "Where did I put my keys?",
        "What items do I have in the garage?",
        "How much did I spend on groceries last month?",
        "List all items that need to be repaired.",
        "Where is my winter coat?",
        "Show me all items that cost more than $100.",
        "What did I buy last week?",
        "How many items are in the kitchen?",
        "Where are the receipts for the items I bought?",
        "What is the total value of my inventory?",
        "Can you remind me where I stored the holiday decorations?",
        "How much have I spent on electronics this year?",
        "What items are in the living room?",
        "List all items that I need to return.",
        "Where did I put the blender?",
        "What is the warranty status of my appliances?",
        "How many items do I have in storage?",
        "What items are due for repair soon?",
        "Can you show me the items I bought on sale?",
        "Where are my tools?",
    ]

    # Corresponding intents with mapping to integers
    label_mapping = {
        'search': 0,
        'count': 1,
        'value': 2,
        'price_range': 3
    }

    y = [
        label_mapping["search"],  # "show me things that cost less than 20"
        label_mapping["count"],  # "how many items do I have in the garage"
        label_mapping["value"],  # "what is the total value of my inventory"
        label_mapping["price_range"],  # "list items that cost more than 50 dollars"
        label_mapping["count"],  # "count all products in storage"
        label_mapping["search"],  # "what items are in the living room"
        label_mapping["value"],  # "how much are my things worth"
        label_mapping["search"],  # "show me things that cost less than 20"
        label_mapping["search"],  # "Where did I put my keys?"
        label_mapping["count"],  # "What items do I have in the garage?"
        label_mapping["value"],  # "How much did I spend on groceries last month?"
        label_mapping["count"],  # "List all items that need to be repaired."
        label_mapping["search"],  # "Where is my winter coat?"
        label_mapping["search"],  # "Show me all items that cost more than $100."
        label_mapping["search"],  # "What did I buy last week?"
        label_mapping["count"],  # "How many items are in the kitchen?"
        label_mapping["search"],  # "Where are the receipts for the items I bought?"
        label_mapping["value"],  # "What is the total value of my inventory?"
        label_mapping[
            "search"
        ],  # "Can you remind me where I stored the holiday decorations?"
        label_mapping["value"],  # "How much have I spent on electronics this year?"
        label_mapping["search"],  # "What items are in the living room?"
        label_mapping["count"],  # "List all items that I need to return."
        label_mapping["search"],  # "Where did I put the blender?"
        label_mapping["search"],  # "What is the warranty status of my appliances?"
        label_mapping["count"],  # "How many items do I have in storage?"
        label_mapping["search"],  # "What items are due for repair soon?"
        label_mapping["search"],  # "Can you show me the items I bought on sale?"
        label_mapping["search"],  # "Where are my tools?"
    ]

    from transformers import DistilBertTokenizerFast

    # Initialize the tokenizer
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    # Tokenize the input data
    tokenized_inputs = tokenizer(X, padding=True, truncation=True, return_tensors="pt")

    # Create a dataset from the tokenized inputs
    train_dataset = Dataset.from_dict({
        'input_ids': tokenized_inputs['input_ids'].tolist(),
        'attention_mask': tokenized_inputs['attention_mask'].tolist(),
        'labels': [int(label) for label in y]  # Ensure labels are integers
    })

    # Initialize and train the NLU processor
    nlu = NLUProcessor()
    nlu.train_model(train_dataset)
    print("NLU model trained and saved successfully")

if __name__ == "__main__":
    main()
