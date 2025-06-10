# MapReduce Midterm Project - Code Architecture Guide

This document provides a comprehensive overview of the codebase structure and implementation patterns used across all levels.

## 📁 Project Structure

```
midterm/
├── Level1-Question7/          # Pixel histogram computation
├── Level1-Question8/          # Telecom call analysis  
├── Level2-Question12/         # Database FULL OUTER JOIN
└── Level3-Question13/         # Apriori frequent itemset mining
```

## 🏗️ Common Architecture Patterns

### 1. **File Naming Convention**
- Main MapReduce jobs: `{task_name}.py` (e.g., `pixel_frequency_counter.py`)
- Input data files: `file01`, `file02`, or descriptive names like `trans01`
- Output organized in subdirectories with consistent naming

### 2. **MapReduce Job Structure**
All MapReduce jobs follow this consistent pattern:

```python
class JobName(MRJob):
    """Clear docstring with Input/Output formats and examples"""
    
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol  
    OUTPUT_PROTOCOL = RawProtocol
    
    def mapper(self, key, value):
        """Process input and emit key-value pairs"""
        
    def combiner(self, key, values):  # Optional
        """Local aggregation to reduce data transfer"""
        
    def reducer(self, key, values):
        """Final aggregation and output formatting"""
```

### 3. **Documentation Standards**
- **Module docstrings**: Clear problem description and solution approach
- **Class docstrings**: Input/Output formats with concrete examples
- **Method docstrings**: Args, Returns/Yields, and clear purpose
- **Inline comments**: Explain complex logic and edge cases

## 🔍 Level-by-Level Breakdown

### Level 1: Basic MapReduce Patterns

**Question 7 - Pixel Histogram**
- Simple count aggregation pattern
- Two variants: basic vs. complete histogram
- Key learning: mapper_final() for ensuring completeness

**Question 8 - Call Duration Analysis** 
- Complex data parsing with dataclasses
- Filtering and aggregation with thresholds
- Key learning: combiner for max() operations

### Level 2: Data Joining

**Question 12 - FULL OUTER JOIN**
- Multi-table data processing
- Complex tuple manipulation for joins
- Key learning: handling missing values in joins

### Level 3: Advanced Algorithm Implementation

**Question 13 - Apriori Algorithm**
- Multi-stage MapReduce pipeline
- Complex candidate generation with validation
- Orchestration of multiple jobs through main driver
- Key learning: algorithm-specific optimizations

## 🎯 Key Implementation Insights

### 1. **Error Handling Patterns**
```python
try:
    # Parse and process data
    pass
except ValueError:
    # Skip malformed records gracefully
    continue
```

### 2. **Data Transfer Optimization**
- Use combiners to reduce network traffic
- Emit minimal data between stages
- Proper use of internal vs. output protocols

### 3. **Algorithm-Specific Optimizations**
- Level 1: Direct item counting
- Level 2: Combinatorial generation (avoid MapReduce overhead)
- Level 3+: Complex MapReduce with subset validation

### 4. **Configuration Management**
```python
def configure_args(self):
    """Standard pattern for command-line arguments"""
    self.add_passthru_arg('--min-sup', type=int)
    self.add_file_arg('--itemset-files', action='append')
```

## ⚡ Performance Considerations

1. **Minimize data transfer**: Use combiners effectively
2. **Avoid unnecessary work**: Early filtering and validation
3. **Choose right approach**: Not everything needs MapReduce
4. **Handle edge cases**: Empty inputs, malformed data, etc.

## 🚀 Running the Code

Each level can be run independently:

```bash
# Level 1 - Pixel counting
python pixel_frequency_counter.py file01 file02 file03

# Level 2 - Database join  
python price_quantity_combiner.py file01 file02

# Level 3 - Apriori algorithm
python main.py trans01 trans02 --min-support 5 --clean
```

## 📋 Best Practices Demonstrated

1. **Consistent code style** across all implementations
2. **Comprehensive documentation** with examples
3. **Robust error handling** for production use
4. **Modular design** with clear separation of concerns
5. **Performance optimization** through proper MapReduce patterns

This architecture provides a solid foundation for understanding and extending MapReduce applications across different problem domains.
