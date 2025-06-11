# Apriori Algorithm with MapReduce

Frequent itemset mining implementation using MapReduce. Processes transaction files to find itemsets that appear frequently together.

## Files

- `main.py` - Main script with algorithm orchestration
- `apriori_core.py` - Core MapReduce functions 
- `itemset_support_counter.py` - Counts itemset support using MapReduce
- `candidate_generator.py` - Generates candidates with Apriori pruning
- `trans01`, `trans02`, `trans03` - Sample transaction data

## Usage

```bash
python main.py [transaction_files...] [options]
```

### Command Line Arguments

**Required:**
- `transaction_files` - One or more transaction files (e.g., `trans01 trans02`)

**Optional:**
- `--min-support N` - Minimum support threshold (default: 4)
- `--runner MODE` - Execution mode: `inline`, `local`, `hadoop` (default: inline)
- `--max-iterations N` - Maximum iterations (default: 100)
- `--clean` - Remove previous output directories
- `--debug` - Show detailed errors and MRJob output
- `--hadoop-args "KEY=VALUE"` - Additional Hadoop arguments (for hadoop runner)
- `--owner NAME` - Job owner (for hadoop runner)

### Examples

```bash
# Basic usage
python main.py trans01 --min-support 3

# Multiple files with local runner
python main.py trans01 trans02 --min-support 5 --runner local

# Debug mode with cleanup
python main.py trans01 --min-support 2 --debug --clean

# Hadoop runner
python main.py trans01 trans02 --min-support 3 --runner hadoop --owner myuser
```

## How It Works

### Algorithm Flow
1. **Level 1:** Count individual items using ItemsetSupportCounter
2. **Level 2:** Generate 2-itemset candidates (combinatorial, no MapReduce)
3. **Level 3+:** Use CandidateGenerator → ItemsetSupportCounter pipeline
4. **Repeat:** Until no new frequent itemsets found

### MapReduce Execution
- **ItemsetSupportCounter:** Maps transactions → counts itemset occurrences → reduces to support counts
- **CandidateGenerator:** Maps frequent itemsets → generates candidates → reduces with Apriori pruning
- **main.py:** Orchestrates the jobs, combines output parts, manages iteration flow

## Output

- `frequent-itemsets/frequent_itemsets_N.txt` - Frequent itemsets by level
- `candidate-itemsets/candidate_itemsets_N.txt` - Generated candidates by level  
- `frequent-itemsets/frequent_itemsets.txt` - Final consolidated results

## Input Format

Transaction files should have format:
```
transaction_id<TAB>item1 item2 item3 ...
```

Example:
```
t001	bread milk eggs
t002	bread butter
t003	milk eggs butter
```

## Notes

- Uses tab-separated output format (itemset<TAB>support_count)
- Supports inline, local, and hadoop MapReduce modes
- Debug mode shows full error traces and MRJob output
