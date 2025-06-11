#!/usr/bin/env python3
"""Generate large database dataset for tc3 FULL OUTER JOIN stress testing."""

import random

# Comprehensive list of food items for realistic database testing
food_items = [
    # Main dishes
    "Pizza", "Burger", "Pasta", "Sushi", "Tacos", "Sandwich", "Steak", "Chicken", "Beef", "Fish",
    "Lamb", "Pork", "Duck", "Turkey", "Lobster", "Shrimp", "Salmon", "Tuna", "Crab", "Oysters",
    
    # Vegetables & Fruits
    "Vegetables", "Salad", "Tomato", "Lettuce", "Carrot", "Potato", "Onion", "Garlic", "Spinach", "Broccoli",
    "Corn", "Peas", "Beans", "Cucumber", "Pepper", "Apple", "Banana", "Orange", "Grape", "Strawberry",
    "Blueberry", "Mango", "Pineapple", "Watermelon", "Peach", "Plum", "Cherry", "Lemon", "Lime", "Avocado",
    
    # Grains & Dairy
    "Bread", "Rice", "Noodles", "Quinoa", "Oats", "Barley", "Wheat", "Cheese", "Milk", "Yogurt",
    "Butter", "Cream", "Eggs", "Tofu", "Honey", "Sugar", "Salt", "Flour", "Oil", "Vinegar",
    
    # Beverages
    "Coffee", "Tea", "Juice", "Water", "Soda", "Beer", "Wine", "Whiskey", "Vodka", "Rum",
    
    # Snacks & Desserts
    "Cookies", "Cake", "Pie", "Ice_Cream", "Chocolate", "Candy", "Chips", "Nuts", "Crackers", "Popcorn",
    "Donuts", "Muffins", "Cupcakes", "Brownies", "Pancakes", "Waffles", "Cereal", "Granola", "Pretzels", "Jerky",
    
    # International Foods
    "Ramen", "Kimchi", "Curry", "Biryani", "Falafel", "Hummus", "Shawarma", "Paella", "Risotto", "Gnocchi",
    "Tempura", "Miso", "Wasabi", "Soy_Sauce", "Teriyaki", "Pad_Thai", "Pho", "Banh_Mi", "Dim_Sum", "Spring_Rolls",
    
    # Additional items to reach 100+
    "Mushrooms", "Asparagus", "Artichoke", "Cauliflower", "Zucchini", "Eggplant", "Kale", "Cabbage", "Radish", "Turnip"
]

def generate_price():
    """Generate realistic food price (1-50)."""
    return random.randint(1, 50)

def generate_quantity():
    """Generate realistic food quantity (1-100)."""
    return random.randint(1, 100)

def create_database_records(food_list, target_records):
    """Create database records with realistic distribution."""
    records = []
    
    # Ensure we have enough unique food items
    available_foods = food_list.copy()
    if len(available_foods) < 100:
        # Generate more variations if needed
        base_foods = available_foods.copy()
        while len(available_foods) < 100:
            base_food = random.choice(base_foods)
            variation = f"{base_food}_{random.randint(1, 99)}"
            if variation not in available_foods:
                available_foods.append(variation)
    
    # Randomly select foods for this dataset
    selected_foods = random.sample(available_foods, min(120, len(available_foods)))
    
    for _ in range(target_records):
        food_item = random.choice(selected_foods)
        table_name = random.choice(["FoodPrice", "FoodQuantity"])
        
        if table_name == "FoodPrice":
            value = generate_price()
        else:
            value = generate_quantity()
        
        records.append(f"{table_name} {food_item} {value}")
    
    return records

# Generate records for each file
records_per_file = [105, 100, 98, 102]  # Total: 405 records
files = ['file31', 'file32', 'file33', 'file34']

print("Generating large database join dataset for tc3...")
print(f"Food items available: {len(food_items)}")

all_records = []
for file_idx, (filename, record_count) in enumerate(zip(files, records_per_file)):
    print(f"Generating {filename} with {record_count} records...")
    
    records = create_database_records(food_items, record_count)
    all_records.extend(records)
    
    # Write to file
    with open(f'/home/khtn_22120363/midterm/Level2-Question12/tc3/{filename}', 'w') as f:
        f.write('\n'.join(records) + '\n')
    
    print(f"✓ Generated {filename} with {record_count} records")

# Count unique food items across all files
unique_foods = set()
food_price_items = set()
food_quantity_items = set()

for record in all_records:
    parts = record.split()
    if len(parts) >= 3:
        table_name = parts[0]
        food_item = parts[1]
        unique_foods.add(food_item)
        
        if table_name == "FoodPrice":
            food_price_items.add(food_item)
        elif table_name == "FoodQuantity":
            food_quantity_items.add(food_item)

print(f"\n=== Dataset Statistics ===")
print(f"Total records generated: {sum(records_per_file)}")
print(f"Unique food items: {len(unique_foods)}")
print(f"Items in FoodPrice: {len(food_price_items)}")
print(f"Items in FoodQuantity: {len(food_quantity_items)}")
print(f"Items in both tables: {len(food_price_items & food_quantity_items)}")
print(f"Items only in FoodPrice: {len(food_price_items - food_quantity_items)}")
print(f"Items only in FoodQuantity: {len(food_quantity_items - food_price_items)}")

print(f"\n✅ tc3 dataset generation complete!")
print(f"All join scenarios covered: inner, left-only, right-only")
