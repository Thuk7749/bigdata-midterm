# Test Case 3: Large Volume Data Stress Test

## Test Scenario
Large dataset processing to test MapReduce performance with high data volume.

## Input Characteristics
- **Files**: 4 input files (file31, file32, file33, file34)
- **Pixel Range**: 0-100
- **Data Size**: 100+ lines total
- **Focus**: MapReduce scalability with large datasets

## Expected Behavior
- Accurate histogram computation with large data volume
- Efficient combiner utilization to minimize data transfer
- Consistent results across distributed files

## Running Instructions

```bash
# Default runner (inline)
python Level1-Question7/pixel_frequency_counter.py \
    Level1-Question7/tc3/file31 Level1-Question7/tc3/file32 \
    Level1-Question7/tc3/file33 Level1-Question7/tc3/file34
```

```bash
# Hadoop runner
python Level1-Question7/pixel_frequency_counter.py \
    Level1-Question7/tc3/file31 Level1-Question7/tc3/file32 \
    Level1-Question7/tc3/file33 Level1-Question7/tc3/file34 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level1-Question7/tc3/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level1-Question7/tc3/results.txt
```
