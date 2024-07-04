# Python / Rust Example

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Rust 1.79 or higher
- Docker

### Installation

### Ingestion

```bash
cd ingestion
poetry install
```

### Pure Python

```bash
cd pure-python-mongo
poetry install
```

### Python Rust

```bash
cd python-rust-mongo/metrics-aggregator
maturin develop

cd ../metrics-ingestion
poetry install

```

## Start mongodb

From the root directory, run the following command:

```bash
./startup.sh
```

then go to ingestion directory and run the following command:

```bash
./startup.sh
```

## Start Pure Python

From the pure-python-mongo directory, run the following command:

```bash
./startup.sh
```

## Start Python Rust

From the python-rust-mongo directory, run the following command:

```bash
./startup.sh
```

## Call the API for Pure Python

```bash
curl --location 'localhost:9090/aggregations?account=account1&aggregation_window=hour'
```

## Call the API for Python Rust

```bash
curl --location 'localhost:8080/aggregations?account=account1&aggregation_window=hour'
```

