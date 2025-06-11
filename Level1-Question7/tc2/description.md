# Test Case 2: Sparse Data with Missing Values

## Test Scenario
Histogram computation with sparse pixel distribution where many values have zero frequency.

## Input Characteristics
- **Files**: 3 input files (file21, file22, file23)
- **Pixel Range**: 0-50 with gaps (only values 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50)
- **Data Size**: 20+ lines total
- **Focus**: Sparse histogram with many missing intermediate values

## Expected Behavior
- Only specific pixel values appear in output
- Correct frequency counts for sparse distribution
- Values not in input don't appear in output

## Running Instructions

```bash
# Default runner (inline)
python Level1-Question7/pixel_frequency_counter.py \
    Level1-Question7/tc2/file21 Level1-Question7/tc2/file22 Level1-Question7/tc2/file23
```

```bash
# Hadoop runner
python Level1-Question7/pixel_frequency_counter.py \
    Level1-Question7/tc2/file21 Level1-Question7/tc2/file22 Level1-Question7/tc2/file23 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level1-Question7/tc2/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level1-Question7/tc2/results.txt
```
