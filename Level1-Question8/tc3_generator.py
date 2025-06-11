#!/usr/bin/env python3
"""Generate large telecom dataset for tc3 stress testing."""

import random
from datetime import datetime, timedelta

# Base phone numbers (will generate variations)
base_phones = [
    "9876543210", "9123456789", "9234567890", "9345678901", "9456789012",
    "9567890123", "9678901234", "9789012345", "9890123456", "9012345678",
    "8765432109", "8876543210", "8987654321", "8098765432", "8109876543",
    "7654321098", "7765432109", "7876543210", "7987654321", "7098765432",
    "6543210987", "6654321098", "6765432109", "6876543210", "6987654321",
    "5432109876", "5543210987", "5654321098", "5765432109", "5876543210",
    "4321098765", "4432109876", "4543210987", "4654321098", "4765432109",
    "3210987654", "3321098765", "3432109876", "3543210987", "3654321098",
    "2109876543", "2210987654", "2321098765", "2432109876", "2543210987",
    "1098765432", "1109876543", "1210987654", "1321098765", "1432109876",
    "9111111111", "9222222222", "9333333333", "9444444444", "9555555555"
]

def generate_phone_variations(base_list, count):
    """Generate phone number variations to reach desired count."""
    phones = base_list.copy()
    while len(phones) < count:
        base = random.choice(base_list)
        # Modify last few digits
        new_phone = base[:-3] + str(random.randint(100, 999))
        if new_phone not in phones:
            phones.append(new_phone)
    return phones[:count]

def random_datetime(start_date, end_date):
    """Generate random datetime between start and end dates."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_hours = random.randint(8, 20)  # Business hours mostly
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    
    return start_date + timedelta(
        days=random_days,
        hours=random_hours,
        minutes=random_minutes,
        seconds=random_seconds
    )

def generate_call_duration(min_minutes=10, max_minutes=180):
    """Generate call duration in minutes."""
    return random.randint(min_minutes, max_minutes)

def generate_call_record(from_phone, to_phone, start_time, duration_minutes, is_std):
    """Generate a single call record."""
    end_time = start_time + timedelta(minutes=duration_minutes)
    std_flag = 1 if is_std else 0
    
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return f"{from_phone}|{to_phone}|{start_str}|{end_str}|{std_flag}"

# Generate phone numbers (50+ unique)
phones = generate_phone_variations(base_phones, 60)
random.shuffle(phones)

# Date range: June 8-14, 2025
start_date = datetime(2025, 6, 8)
end_date = datetime(2025, 6, 14)

# Generate records for each file
records_per_file = [55, 50, 52, 48]  # Total: 205 records
files = ['file31', 'file32', 'file33', 'file34']

for file_idx, (filename, record_count) in enumerate(zip(files, records_per_file)):
    records = []
    
    for _ in range(record_count):
        from_phone = random.choice(phones)
        to_phone = random.choice([p for p in phones if p != from_phone])
        start_time = random_datetime(start_date, end_date)
        duration = generate_call_duration()
        is_std = random.choice([True, False])  # Mix of STD and local calls
        
        record = generate_call_record(from_phone, to_phone, start_time, duration, is_std)
        records.append(record)
    
    # Write to file
    with open(f'/home/khtn_22120363/midterm/Level1-Question8/tc3/{filename}', 'w') as f:
        f.write('\n'.join(records) + '\n')
    
    print(f"Generated {filename} with {record_count} records")

print(f"Total records generated: {sum(records_per_file)}")
print(f"Unique phone numbers: {len(phones)}")
