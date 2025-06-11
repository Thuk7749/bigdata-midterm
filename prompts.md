
## Pixel Frequency Counter Overthinked

```bash
cd Level1-Question7 && python pixel_frequency_counter_overthinked.py file01 file02 file03 -r hadoop --output-dir results
```

```bash
# Same as `hdfs dfs -get`
hdfs dfs -copyToLocal ./results/part* ./results && hdfs dfs -rm -r ./results
```

## Call Duration Filter

```bash
cd Level1-Question8 && python call_duration_filter.py file01 file02 -r hadoop --output-dir results
```

```bash
hdfs dfs -copyToLocal ./results/part* ./results && hdfs dfs -rm -r ./results
```

## Price Quantity Combiner

```bash
cd Level2-Question12 && python price_quantity_combiner.py file01 file02 -r hadoop --output-dir results
```

```bash
hdfs dfs -copyToLocal ./results/part* ./results && hdfs dfs -rm -r ./results
```

## Apriori Algorithm

### Test with local runner

```bash
cd Level3-Question13 && python main.py trans01 trans02 --min-support-decimal 0.20 --runner local --clean
```

### Test with Hadoop runner

```bash
cd Level3-Question13 && \
    sudo rm -rf candidate-itemsets && \
    sudo rm -rf frequent-itemsets && \
    mkdir candidate-itemsets && \
    mkdir frequent-itemsets && \
    python main.py trans01 trans02 --min-support-decimal 0.20 --runner hadoop --debug
```
