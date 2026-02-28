import os
import subprocess
from pathlib import Path
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Give the model project context
file_tree = subprocess.check_output(["find", "git_dev_metrics", "-name", "*.py"]).decode()

# Read all source files into context
codebase = ""
for path in Path("git_dev_metrics").rglob("*.py"):
    codebase += f"\n\n### {path} ###\n{path.read_text()}"

vision = Path("VISION.md").read_text() if Path("VISION.md").exists() else ""
agents = Path("AGENTS.md").read_text() if Path("AGENTS.md").exists() else ""

prompt = f"""
You are a developer working on this Python project.

## Guidelines
{agents}

## Vision
{vision}

## File Structure
{file_tree}

## Codebase
{codebase}

## Issue to fix
Title: {os.getenv("ISSUE_TITLE")}
Body: {os.getenv("ISSUE_BODY")}

Respond with a unified diff patch only. No explanation. No markdown fences.
"""

model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content(prompt)

with open(os.getenv("PATCH_OUTPUT_PATH", "ai.patch"), "w") as f:
    f.write(response.text)
