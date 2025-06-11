# Apriori Algorithm Implementation with MapReduce

This directory contains a comprehensively refactored implementation of the Apriori algorithm for frequent itemset mining using MapReduce, featuring advanced logging, state management, and debugging capabilities.

## Overview

The implementation consists of four main components with clean architectural separation:

1. **`main.py`** - Orchestrates the complete Apriori algorithm with enhanced logging and debug support
2. **`apriori_core.py`** - Core MapReduce computation functions (separated for better maintainability)
3. **`itemset_support_counter.py`** - Counts support for itemsets using MapReduce
4. **`candidate_generator.py`** - Generates candidate itemsets with Apriori pruning

## Key Features

### 🚀 **Enhanced Algorithm Architecture**
- **AprioriState Class**: Lightweight state management for algorithm progression
- **Step-based Execution**: Clean, modular function decomposition
- **Comprehensive Logging**: Detailed input/output file tracking and generation strategies
- **Error Handling**: Robust exception handling with optional debug traces

### 🐛 **Advanced Debug Support**
- **Debug Mode**: `--debug` flag for detailed error reporting and MRJob output visibility
- **Stack Traces**: Full error context when troubleshooting issues
- **File Tracking**: Detailed logging of input files, output files, and processing steps

### 📊 **Professional Logging**
- **Visual Hierarchy**: Consistent icon-based indicators for different message types
- **Strategy Context**: Clear explanations of algorithm approaches used at each level
- **Balanced Reporting**: Equal detail for both frequent itemset finding and candidate generation
- **Progress Tracking**: Real-time feedback on algorithm progression

## Key Files

- **`main.py`** - Main driver with refactored step-based architecture
- **`apriori_core.py`** - Core MapReduce computation functions
- **`itemset_support_counter.py`** - MapReduce job for counting itemset support
- **`candidate_generator.py`** - MapReduce job for generating candidates with subset validation
- **`trans*`** - Sample transaction files for testing

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
