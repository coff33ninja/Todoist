import os
import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
)


class NLUModel:
    def __init__(
        self,
        model_name="distilbert-base-uncased",
        model_save_path="ai_models/nlu_model",
    ):
        self.model_name = model_name
        self.model_save_path = model_save_path
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
        self.model = DistilBertForSequenceClassification.from_pretrained(model_name)

    def load_data(self, data_path):
        """Load dataset from a CSV file."""
        df = pd.read_csv(data_path)
        intent_labels = {
            intent: idx for idx, intent in enumerate(df["intent"].unique())
        }
        df["label"] = df["intent"].map(intent_labels)

        train_texts = df["query"].tolist()
        train_labels = df["label"].tolist()

        return train_texts, train_labels, intent_labels

    def train(self, data_path, batch_size=8, epochs=3):
        """Train the NLU model."""
        train_texts, train_labels, intent_labels = self.load_data(data_path)

        train_encodings = self.tokenizer(train_texts, truncation=True, padding=True)
        train_dataset = Dataset.from_dict(
            {
                "input_ids": train_encodings["input_ids"],
                "attention_mask": train_encodings["attention_mask"],
                "labels": train_labels,
            }
        )

        training_args = TrainingArguments(
            output_dir="ai_models/results",
            evaluation_strategy="epoch",
            save_strategy="epoch",
            per_device_train_batch_size=batch_size,
            num_train_epochs=epochs,
            weight_decay=0.01,
            logging_dir="ai_models/logs",
            logging_steps=10,
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
        )

        trainer.train()

        # Save the trained model
        os.makedirs(self.model_save_path, exist_ok=True)
        self.model.save_pretrained(self.model_save_path)
        self.tokenizer.save_pretrained(self.model_save_path)

        print(f"[✅] Model saved to {self.model_save_path}")

    def predict_intent(self, text):
        """Predict the intent of a given text."""
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        predicted_label = torch.argmax(outputs.logits).item()
        return predicted_label
