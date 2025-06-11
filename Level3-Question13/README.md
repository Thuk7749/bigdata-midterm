# Apriori Algorithm with MapReduce

Frequent itemset mining implementation using MapReduce. Processes transaction files to find itemsets that appear frequently together.

## Files

- `main.py` - Main script with algorithm orchestration
- `apriori_core.py` - Core MapReduce functions 
- `decimal_support_converter.py` - Converts decimal support to count using MapReduce
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
- `--min-support N` - Minimum support threshold (direct count)
- `--min-support-decimal X` - Minimum support as decimal (0.0-1.0, default: 0.5 if no support specified)
- `--runner MODE` - Execution mode: `inline`, `local`, `hadoop` (default: inline)
- `--max-iterations N` - Maximum iterations (default: 100)
- `--clean` - Remove previous output directories
- `--debug` - Show detailed errors and MRJob output
- `--hadoop-args "KEY=VALUE"` - Additional Hadoop arguments (for hadoop runner)
- `--owner NAME` - Job owner (for hadoop runner)

**Note:** You cannot specify both `--min-support` and `--min-support-decimal` simultaneously.

### Examples

```bash
# Basic usage with count-based support
python main.py trans01 --min-support 3

# Using decimal support (30% of transactions)
python main.py trans01 --min-support-decimal 0.3

# Default behavior (uses 0.5 decimal support if no support specified)
python main.py trans01

# Multiple files with local runner
python main.py trans01 trans02 --min-support 5 --runner local

# Debug mode with cleanup
python main.py trans01 --min-support-decimal 0.2 --debug --clean

# Hadoop runner with decimal support
python main.py trans01 trans02 --min-support-decimal 0.4 --runner hadoop --owner myuser
```

## How It Works

### Algorithm Flow
0. **Level 0:** Convert decimal support (relative support) to count (absolute support) using DecimalSupportConverter (if decimal support specified)
1. **Level 1:** Count individual items using ItemsetSupportCounter
2. **Level 2:** Generate 2-itemset candidates (combinatorial, no MapReduce)
3. **Level 3+:** Use CandidateGenerator → ItemsetSupportCounter pipeline
4. **Repeat:** Until no new frequent itemsets found

### MapReduce Execution
- **DecimalSupportConverter:** Maps transactions → counts total transactions → calculates support count (Level 0)
- **ItemsetSupportCounter:** Maps transactions → counts itemset occurrences → reduces to support counts
- **CandidateGenerator:** Maps frequent itemsets → generates candidates → reduces with Apriori pruning
- **main.py:** Orchestrates the jobs, combines output parts, manages iteration flow

## Output

- `frequent-itemsets/frequent_itemsets_N.txt` - Frequent itemsets by level
- `candidate-itemsets/candidate_itemsets_N.txt` - Generated candidates by level  
- `frequent-itemsets/frequent_itemsets.txt` - Final consolidated results

## Support Specification

The algorithm supports two ways to specify minimum support:

1. **Direct Count** (`--min-support N`): Specify the exact minimum number of transactions
2. **Decimal Support** (`--min-support-decimal X`): Specify as a fraction (0.0-1.0) of total transactions

If neither is specified, the default is `--min-support-decimal 0.5` (50% of transactions).

The decimal support is converted to an actual count using the DecimalSupportConverter MapReduce job, which:
- Counts total transactions across all input files
- Calculates `floor(decimal_support * total_transactions)`
- Returns the integer support count for use in the algorithm

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
- Supports both direct count and decimal support specification
- Decimal support uses MapReduce to calculate exact counts from transaction totals
- Supports inline, local, and hadoop MapReduce modes
- Debug mode shows full error traces and MRJob output
- Cannot specify both `--min-support` and `--min-support-decimal` simultaneously
