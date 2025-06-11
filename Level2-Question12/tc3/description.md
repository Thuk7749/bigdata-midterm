# Test Case 3: Large Database Join Operation

## Test Scenario
Large-scale database join with numerous food items distributed across multiple files to test MapReduce efficiency.

## Input Characteristics
- **Files**: 4 input files (file31, file32, file33, file34)
- **Food Items**: 100+ unique food items
- **Data Size**: 400+ table records total
- **Focus**: MapReduce scalability with large database operations

## Expected Behavior
- Efficient processing of large table join operations
- Accurate join results across distributed mappers
- Correct handling of combiner optimization for data transfer reduction

## Running Instructions

```bash
# Default runner (inline)
python Level2-Question12/price_quantity_combiner.py \
    Level2-Question12/tc3/file31 Level2-Question12/tc3/file32 \
    Level2-Question12/tc3/file33 Level2-Question12/tc3/file34
```

```bash
# Hadoop runner
python Level2-Question12/price_quantity_combiner.py \
    Level2-Question12/tc3/file31 Level2-Question12/tc3/file32 \
    Level2-Question12/tc3/file33 Level2-Question12/tc3/file34 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level2-Question12/tc3/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level2-Question12/tc3/results.txt
```
