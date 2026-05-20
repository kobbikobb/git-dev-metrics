#!/bin/bash

set -e

uv run pytest tests/ --cov=git_dev_metrics --cov-report=term-missing -v
