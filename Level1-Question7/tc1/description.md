# Test Case 1: Basic Functionality with Edge Values

## Test Scenario
Basic histogram computation with edge pixel values including 0 and complete small range coverage.

## Input Characteristics
- **Files**: 3 input files (file11, file12, file13)
- **Pixel Range**: 0-15
- **Data Size**: 15+ lines total
- **Focus**: Includes pixel value 0 and edge values

## Expected Behavior
- All pixel values 0-15 appear in output
- Pixel value 0 included with correct count
- Output format: tab-separated "pixel_value\tcount"

## Running Instructions

```bash
# Default runner (inline)
python Level1-Question7/pixel_frequency_counter.py \
    Level1-Question7/tc1/file11 Level1-Question7/tc1/file12 Level1-Question7/tc1/file13
```

```bash
# Hadoop runner
python Level1-Question7/pixel_frequency_counter.py \
    Level1-Question7/tc1/file11 Level1-Question7/tc1/file12 Level1-Question7/tc1/file13 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level1-Question7/tc1/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level1-Question7/tc1/results.txt
```
