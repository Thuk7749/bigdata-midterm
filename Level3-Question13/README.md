# Apriori Algorithm Implementation with MapReduce

This directory contains a complete implementation of the Apriori algorithm for frequent itemset mining using MapReduce.

## Overview

The implementation consists of three main components:

1. **`itemset_support_counter.py`** - Counts support for itemsets
2. **`candidate_generator.py`** - Generates candidate itemsets with pruning
3. **`main.py`** - Orchestrates the complete Apriori algorithm

## Key Files

- `main.py` - Main driver that coordinates the entire Apriori process
- `itemset_support_counter.py` - MapReduce job for counting itemset support
- `candidate_generator.py` - MapReduce job for generating candidates with subset validation
- `trans*` - Sample transaction files for testing
- `test_sample.txt`, `complex_test.txt` - Additional test datasets

## How to Run

```bash
# Basic usage with minimum support of 3
python main.py trans01 --min-support 3

# Multiple files with different runner mode
python main.py trans01 trans02 --min-support 5 --runner local

# Clean previous outputs and limit iterations
python main.py trans01 --min-support 2 --clean --max-iterations 5
```

## Algorithm Flow

1. **Level 1**: Count individual item frequencies
2. **Level 2**: Generate 2-itemset candidates using combinatorial approach
3. **Level 3+**: Use MapReduce candidate generation with:
   - Prefix-based generation
   - Subset validation
   - Apriori principle pruning

## Output

- `frequent-itemsets/` - Contains frequent itemsets by level
- `candidate-itemsets/` - Contains generated candidates by level
- `frequent_itemsets.txt` - Final consolidated results

## Technical Notes

- Uses tab-separated format for itemset-support pairs
- Implements proper Apriori pruning for efficiency
- Supports multiple MapReduce execution modes (inline, local, hadoop)
- Handles edge cases and malformed input gracefully
