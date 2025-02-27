#!/usr/bin/env python
"""
Enhanced NLU Training Script with improved data handling, validation, and testing.
"""
import os
import sys
import argparse
import sqlite3
import pandas as pd
from datasets import Dataset
from transformers import DistilBertTokenizerFast
from sklearn.model_selection import train_test_split
import torch

# Ensure the repository is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai.nlu_processor import NLUProcessor


def load_and_prepare_data(data_path=None, label_mapping=None):
    """Load training data from file or use default examples if no file provided."""
    if data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
        df["label"] = df["intent"].map(label_mapping)
        df = df.dropna(subset=["label"])
        return df["query"].tolist(), df["label"].tolist()

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

    y = [
        0,
        1,
        2,
        3,
        1,
        0,
        2,
        3,
        0,
        0,
        2,
        4,
        0,
        3,
        5,
        1,
        0,
        2,
        0,
        2,
        0,
        4,
        0,
        4,
        1,
        4,
        5,
        0,
    ]

    return X, y


def create_dataset(queries, labels, tokenizer):
    """Create a Dataset object from queries and labels."""
    tokenized_inputs = tokenizer(
        queries, padding=True, truncation=True, return_tensors="pt"
    )
    return Dataset.from_dict(
        {
            "input_ids": tokenized_inputs["input_ids"].tolist(),
            "attention_mask": tokenized_inputs["attention_mask"].tolist(),
            "labels": [int(label) for label in labels],
        }
    )


def mock_db_connection():
    """Create an in-memory SQLite database with the 'items' table and sample data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create the 'items' table
    cursor.execute(
        """
        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            quantity INTEGER,
            location TEXT,
            category TEXT,
            tags TEXT,
            purchase_date TEXT,
            needs_repair INTEGER
        )
    """
    )

    # Optional: Insert sample data for testing
    sample_items = [
        ("jacket", 50.0, 1, "closet", "clothing", "winter", "2023-01-15", 0),
        ("hammer", 15.0, 2, "garage", "tools", "hand tool", "2022-06-10", 0),
        ("lawnmower", 200.0, 1, "garage", "tools", "power tool", "2021-05-20", 1),
    ]
    cursor.executemany(
        """
        INSERT INTO items (name, price, quantity, location, category, tags, purchase_date, needs_repair)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        sample_items,
    )

    conn.commit()
    return conn


def main():
    parser = argparse.ArgumentParser(description="Train an enhanced NLU model.")
    parser.add_argument("--data", type=str, help="Path to CSV training data (optional)")
    parser.add_argument(
        "--epochs", type=int, default=3, help="Number of training epochs"
    )
    parser.add_argument(
        "--batch_size", type=int, default=16, help="Training batch size"
    )
    parser.add_argument(
        "--model_dir",
        type=str,
        default="ai_models/nlu_model",
        help="Directory to save the trained model",
    )
    args = parser.parse_args()

    # os.makedirs(os.path.dirname(args.model_dir), exist_ok=True)

    label_mapping = {
        "search": 0,
        "count": 1,
        "value": 2,
        "price_range": 3,
        "repair": 4,
        "purchase_history": 5,
    }

    queries, labels = load_and_prepare_data(args.data, label_mapping)
    print(f"[INFO] Loaded {len(queries)} training examples")

    queries_train, queries_val, labels_train, labels_val = train_test_split(
        queries, labels, test_size=0.2, random_state=42
    )
    print(
        f"[INFO] Training on {len(queries_train)}, validating on {len(queries_val)} examples"
    )

    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    train_dataset = create_dataset(queries_train, labels_train, tokenizer)
    val_dataset = create_dataset(queries_val, labels_val, tokenizer)

    nlu = NLUProcessor(model_path=args.model_dir)
    nlu.train_model(
        train_dataset,
        eval_dataset=val_dataset,
        epochs=args.epochs,
        batch_size=args.batch_size,
        output_dir="ai_models/temp_nlu_model",
    )

    print(f"[SUCCESS] NLU model trained and saved to {args.model_dir}")

    # Test the model with some sample queries
    test_queries = [
        "Where's my jacket?",
        "How many tools in the garage?",
        "What needs fixing?",
        "Show me items over $50"
    ]
    
    # Create a mock database connection for testing
    conn = mock_db_connection()
    cursor = conn.cursor()
    
    # Test each query
    for q in test_queries:
        print(f"Query: {q}")
        
        # Process the query using our NLU processor
        try:
            result = nlu.process_natural_language_query(q, cursor)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error processing query: {str(e)}")
        
        print("-" * 50)


if __name__ == "__main__":
    main()