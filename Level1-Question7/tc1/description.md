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
cd /home/khtn_22120363/midterm/Level1-Question7/tc1
python ../pixel_frequency_counter.py file11 file12 file13
```
