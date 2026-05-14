# Wizard-driven CLI

## Problem

Users had to memorise flags (org, repo, period, output path) to generate any report. The learning curve was a barrier to ad-hoc analysis.

## Options

Pure flag-based CLI (rejected — steep learning curve, poor discoverability). Wizard-driven with flag fallback (chosen).

## Solution

Commands accept simple flags but fall back to interactive prompts (wizards) when arguments are omitted. Users are guided through month selection, repo picking, and report generation.

## Consequences

Harder for automated/CI usage — the wizard prompts expect a human at the terminal. That trade-off is accepted; the primary audience is a developer running one-off analysis.
