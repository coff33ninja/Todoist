from core.inventory_manager import InventoryManager
import random

# Function to generate variants of given away items
def generate_variants(item, num_variants=10):  # Increased default number of variants
    variants = []
    for _ in range(num_variants):
        variant = item.copy()
        # Randomly modify the name and description
        variant['name'] = variant['name'] + ' Variant ' + str(random.randint(1, 100))
        variant['description'] = variant['description'] + ' - Modified'
        # Additional random modifications
        variant['price'] = round(random.uniform(1.0, 100.0), 2)  # Random price
        variant['category'] = random.choice(['Electronics', 'Clothing', 'Food', 'Books'])  # Random category
        variants.append(variant)
    return variants

def main():
    inventory_manager = InventoryManager(db_path='inventory.db')
    items_given_away = inventory_manager.get_items_given_away()
    all_variants = []
    for item in items_given_away:
        variants = generate_variants(item)
        all_variants.extend(variants)
    
    # Print or save the variants for training
    for variant in all_variants:
        print(variant)

if __name__ == "__main__":
    main()
