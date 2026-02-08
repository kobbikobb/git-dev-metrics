#!/bin/bash

set -e

uv run python -m git_dev_metrics.cli --org facebook --repo react
