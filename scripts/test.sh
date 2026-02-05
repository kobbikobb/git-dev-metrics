#!/bin/bash

set -e

uv run pytest tests/ -v
