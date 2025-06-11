# Test Case 1: Basic Full Outer Join

## Test Scenario
Basic FULL OUTER JOIN between FoodPrice and FoodQuantity tables with complete coverage of join scenarios.

## Input Characteristics
- **Files**: 3 input files (file11, file12, file13)
- **Join Types**: All join scenarios (inner, left-only, right-only)
- **Data Size**: 15+ table records total
- **Focus**: Complete join operation coverage with balanced table data

## Expected Behavior
- Items in both tables appear with both values
- Items only in FoodPrice appear with "null" quantity
- Items only in FoodQuantity appear with "null" price
- Output format: space-separated "item_name price quantity"

## Running Instructions

```bash
# Default runner (inline)
python Level2-Question12/price_quantity_combiner.py \
    Level2-Question12/tc1/file11 Level2-Question12/tc1/file12 Level2-Question12/tc1/file13
```

```bash
# Hadoop runner
python Level2-Question12/price_quantity_combiner.py \
    Level2-Question12/tc1/file11 Level2-Question12/tc1/file12 Level2-Question12/tc1/file13 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level2-Question12/tc1/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level2-Question12/tc1/results.txt
```
