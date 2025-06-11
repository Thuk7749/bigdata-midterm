# Test Case 2: Mixed Call Types and Maximum STD Call Duration

## Test Scenario
Mixed STD and local calls where phones have multiple STD calls but only the maximum duration per phone is considered.

## Input Characteristics
- **Files**: 3 input files (file21, file22, file23)
- **Call Pattern**: Multiple STD calls per phone number with varying durations
- **Data Size**: 30+ call records total
- **Focus**: Maximum duration selection among multiple STD calls per phone

## Expected Behavior
- Only maximum STD call duration per phone number is considered
- Local calls (STDFlag=0) are ignored in duration calculation
- Only phones with maximum STD call >60 minutes appear in output

## Running Instructions

```bash
# Default runner (inline)
python Level1-Question8/call_duration_filter.py \
    Level1-Question8/tc2/file21 Level1-Question8/tc2/file22 Level1-Question8/tc2/file23
```

```bash
# Hadoop runner
python Level1-Question8/call_duration_filter.py \
    Level1-Question8/tc2/file21 Level1-Question8/tc2/file22 Level1-Question8/tc2/file23 \
    -r hadoop --output-dir results && \
    hdfs dfs -copyToLocal results/part-* Level1-Question8/tc2/results.txt && \
    hdfs dfs -rm -r results && \
    cat Level1-Question8/tc2/results.txt
```
