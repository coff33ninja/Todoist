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
        "show me things that cost less than 20"
    ]

    # Corresponding intents with mapping to integers
    label_mapping = {
        'search': 0,
        'count': 1,
        'value': 2,
        'price_range': 3
    }
    
    y = [
        label_mapping['search'],
        label_mapping['count'],
        label_mapping['value'],
        label_mapping['price_range'],
        label_mapping['count'],
        label_mapping['search'],
        label_mapping['value'],
        label_mapping['price_range']
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
