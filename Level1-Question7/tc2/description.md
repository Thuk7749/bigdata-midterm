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
cd /home/khtn_22120363/midterm/Level1-Question7/tc2
python ../pixel_frequency_counter.py file21 file22 file23
```
