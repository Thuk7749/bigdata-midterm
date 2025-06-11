
## Show Python version and install dependencies

```powershell
source ../.venv/bin/activate && \
    python --version && \
    pip list
```

## Command line arguments

```powershell
python main.py --help
```

## Run the testcase in local environment

```powershell
sudo rm -rf candidate-itemsets && \
    sudo rm -rf frequent-itemsets && \
    mkdir candidate-itemsets && \
    mkdir frequent-itemsets && \
    python main.py \
        testcase1/file1.txt testcase1/file2.txt testcase1/file3.txt \
        --min-support-decimal 0.25 \
        --runner local
```

```powershell
sudo rm -rf candidate-itemsets && \
    sudo rm -rf frequent-itemsets && \
    mkdir candidate-itemsets && \
    mkdir frequent-itemsets && \
    python main.py \
        testcase3/file1.txt testcase3/file2.txt testcase3/file3.txt \
        --min-support-decimal 0.05 \
        --runner local
```

## Run the testcase in hadoop environment

```powershell
sudo rm -rf candidate-itemsets && \
    sudo rm -rf frequent-itemsets && \
    mkdir candidate-itemsets && \
    mkdir frequent-itemsets && \
    python main.py \
        testcase3/file1.txt testcase3/file2.txt testcase3/file3.txt \
        --min-support-decimal 0.05 \
        --runner hadoop
```