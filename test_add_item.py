import requests
import json

def test_add_item():
    # The API endpoint
    url = "http://localhost:5000/api/items"

    # Test data
    item_data = {
        "name": "Test Laptop",
        "description": "A test laptop for inventory",
        "quantity": 1,
        "price": 999.99,
        "acquisition_type": "purchase",
        "purchase_date": "2024-03-20",
        "warranty_expiry": "2025-03-20",
        "location": "Office",
        "condition": "new",
        "notes": "First inventory item"
    }

    try:
        # Make the POST request
        response = requests.post(url, json=item_data)
        
        # Print the response status and content
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 201:
            print("\nItem added successfully!")
            
            # Let's also verify by getting all items
            get_response = requests.get(url)
            print("\nCurrent Inventory:")
            print(json.dumps(get_response.json(), indent=2))
        else:
            print("\nFailed to add item.")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_add_item()