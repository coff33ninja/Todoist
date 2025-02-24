import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.nlu_processor import NLUProcessor

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
        "show me things that cost less than 20"
    ]

    # Corresponding intents
    y = [
        'search',
        'count',
        'value',
        'price_range',
        'count',
        'search',
        'value',
        'price_range'
    ]

    # Initialize and train the NLU processor
    nlu = NLUProcessor()
    nlu.train_model(X, y)
    print("NLU model trained and saved successfully")

if __name__ == "__main__":
    main()
