#!/usr/bin/env python
"""
Enhanced NLU Training Script with improved data handling and training process.
"""
import os
import sys
import argparse
import pandas as pd
from datasets import Dataset
from transformers import DistilBertTokenizerFast

# Ensure the repository is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai.nlu_processor import NLUProcessor

def load_and_prepare_data(data_path=None, label_mapping=None):
    """Load training data from file or use default examples if no file provided."""
    if data_path and os.path.exists(data_path):
        # Read from CSV file if it exists
        df = pd.read_csv(data_path)
        df["label"] = df["intent"].map(label_mapping)
        df = df.dropna(subset=["label"])
        return df["query"].tolist(), df["label"].tolist()
    
    # Default training examples if no file provided
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

    # Default labels
    y = [
        0,  # search
        1,  # count
        2,  # value
        3,  # price_range
        1,  # count
        0,  # search
        2,  # value
        3,  # price_range
        0,  # search
        1,  # count
        2,  # value
        1,  # count
        0,  # search
        3,  # price_range
        0,  # search
        1,  # count
        0,  # search
        2,  # value
        0,  # search
        2,  # value
        0,  # search
        1,  # count
        0,  # search
        0,  # search
        1,  # count
        0,  # search
        0,  # search
        0,  # search
    ]
    
    return X, y

def create_dataset(queries, labels, tokenizer):
    """Create a Dataset object from queries and labels."""
    tokenized_inputs = tokenizer(
        queries,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )
    
    return Dataset.from_dict({
        'input_ids': tokenized_inputs['input_ids'].tolist(),
        'attention_mask': tokenized_inputs['attention_mask'].tolist(),
        'labels': [int(label) for label in labels]
    })

def main():
    parser = argparse.ArgumentParser(description="Train an enhanced NLU model.")
    parser.add_argument(
        "--data",
        type=str,
        help="Path to CSV training data (optional)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="Training batch size"
    )
    parser.add_argument(
        "--model_dir",
        type=str,
        default="ai_models",
        help="Directory to save the trained model"
    )
    args = parser.parse_args()

    # Ensure model directory exists
    os.makedirs(args.model_dir, exist_ok=True)

    # Define intent to label mapping
    label_mapping = {
        'search': 0,
        'count': 1,
        'value': 2,
        'price_range': 3
    }

    # Load and prepare training data
    queries, labels = load_and_prepare_data(args.data, label_mapping)
    print(f"[ℹ️] Loaded {len(queries)} training examples")

    # Initialize tokenizer and create dataset
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    train_dataset = create_dataset(queries, labels, tokenizer)

    # Initialize and train the model
    model_path = os.path.join(args.model_dir, "nlu_model.pkl")
    nlu = NLUProcessor(model_path=model_path)
    nlu.train_model(train_dataset)
    
    print(f"[✅] NLU model trained and saved to {model_path}")

if __name__ == "__main__":
    main()