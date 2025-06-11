# Test Case 2: Unbalanced Tables and Missing Values

## Test Scenario
Unbalanced table sizes where one table has significantly more entries, testing scenarios with many missing values.

## Input Characteristics
- **Files**: 3 input files (file21, file22, file23)
- **Table Balance**: More FoodPrice records than FoodQuantity records
- **Data Size**: 25+ table records total
- **Focus**: Unbalanced join with many left-only and right-only matches

## Expected Behavior
- Items only in FoodPrice appear with "null" quantity
- Items only in FoodQuantity appear with "null" price
- Correct handling of heavily unbalanced table distributions

## Running Instructions
```bash
cd /home/khtn_22120363/midterm/Level2-Question12/tc2
python ../price_quantity_combiner.py file21 file22 file23
```
