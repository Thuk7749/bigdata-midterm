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
cd /home/khtn_22120363/midterm/Level1-Question7/tc3
python ../pixel_frequency_counter.py file31 file32 file33 file34
```
