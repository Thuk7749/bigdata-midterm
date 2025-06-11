# MapReduce Algorithms - Quick Start

⚠️ **Use Python 3.10.12** - `mrjob` has compatibility issues with newer versions! (smalller version may still work, but 3.10.12 is already tested)

## Setup

```bash
# Install venv support & create environment
sudo apt install python3.10-venv
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Question 13: Apriori Algorithm (Main Focus)

### Quick Test
```bash
cd Level3-Question13
python main.py trans01 trans02 --min-support 3 --runner local --clean
```

### Command Options
```bash
python main.py [files...] [--min-support N] [--runner MODE] [--clean] [--debug]
```

### Examples

**Basic:**
```bash
python main.py trans01 --min-support 3
```

**Debug:**
```bash
python main.py trans01 trans02 --min-support 3 --runner local --debug --clean
```

**Hadoop:**

(*The `rm` and `mkdir` are not required if your local does not have permission issues.*)

```bash
cd Level3-Question13 && \
    sudo rm -rf candidate-itemsets && \
    sudo rm -rf frequent-itemsets && \
    mkdir candidate-itemsets && \
    mkdir frequent-itemsets && \
    python main.py trans01 trans02 --min-support 5 --runner hadoop
```

### Output
- `frequent-itemsets/frequent_itemsets.txt` - Final results
- `candidate-itemsets/` - Generated candidates by level

## Troubleshooting

**Python version issues:** Use `python3.10 -m venv .venv && source .venv/bin/activate`  
**MRJob errors:** `pip install mrjob==0.7.4`  
**Permission errors:** Use `sudo rm -rf` for cleaning directories  
**Debug errors:** Add `--debug` flag
