# Test Case 1: Basic STD Call Duration Filtering

## Test Scenario
Basic filtering of phone numbers with STD calls exceeding 60 minutes, including edge cases around the threshold.

## Input Characteristics
- **Files**: 3 input files (file11, file12, file13)
- **Call Type**: All calls are STD calls (STDFlag=1)
- **Call Duration Range**: 50-120 minutes per call
- **Data Size**: 20+ call records total
- **Focus**: Threshold boundary testing (exactly 60, slightly above/below)

## Expected Behavior
- Only phone numbers with >60 minutes total STD time appear in output
- Phone numbers with exactly 60 minutes are excluded
- Output format: tab-separated "phone_number\tduration_minutes"

## Running Instructions

```bash
# Default runner (inline)
python Level1-Question8/call_duration_filter.py \
    Level1-Question8/tc1/file11 Level1-Question8/tc1/file12 Level1-Question8/tc1/file13
```

```bash
# Hadoop runner
python Level1-Question8/call_duration_filter.py \
    Level1-Question8/tc1/file11 Level1-Question8/tc1/file12 Level1-Question8/tc1/file13 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level1-Question8/tc1/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level1-Question8/tc1/results.txt
```
