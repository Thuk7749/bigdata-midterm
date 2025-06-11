# Test Case 3: Large Dataset with High STD Usage

## Test Scenario
Large telecom dataset with numerous phone numbers and varying STD call patterns to test MapReduce scalability.

## Input Characteristics
- **Files**: 4 input files (file31, file32, file33, file34)
- **Phone Numbers**: 50+ unique phone numbers
- **Data Size**: 200+ call records total
- **Focus**: MapReduce performance with large telecom datasets

## Expected Behavior
- Efficient processing of large call record volumes
- Accurate aggregation across multiple files and mappers
- Correct identification of heavy STD users (>60 minutes)

## Running Instructions

```bash
# Default runner (inline)
python Level1-Question8/call_duration_filter.py \
    Level1-Question8/tc3/file31 Level1-Question8/tc3/file32 \
    Level1-Question8/tc3/file33 Level1-Question8/tc3/file34
```

```bash
# Hadoop runner
python Level1-Question8/call_duration_filter.py \
    Level1-Question8/tc3/file31 Level1-Question8/tc3/file32 \
    Level1-Question8/tc3/file33 Level1-Question8/tc3/file34 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level1-Question8/tc3/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level1-Question8/tc3/results.txt
```
