#!/bin/bash

set -e

echo "Running ruff check --fix..."
uv run ruff check git_dev_metrics --fix

echo "Running ruff format..."
uv run ruff format git_dev_metrics

echo "Code formatting complete!"
