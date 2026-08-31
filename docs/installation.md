# Installation Guide

## Requirements

- Python 3.8 or higher
- pip package manager

## Step 1: Clone Repository

```bash
git clone https://github.com/walidddhony-rgb/SPEECHTIME.git
cd SPEECHTIME
```

## Step 2: Create Virtual Environment (Optional)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Install Package (Optional)

```bash
pip install -e .
```

## Verify Installation

```bash
python -m src.transcriber --help
```

You should see the help message.

## Troubleshooting

### NumPy Installation Error

```bash
pip install --upgrade pip
pip install numpy
```

### SciPy Installation Error

```bash
pip install scipy
```

### Permission Error

```bash
pip install --user -r requirements.txt
```