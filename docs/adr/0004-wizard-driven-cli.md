# Wizard-driven CLI over pure flag-based

Commands accept simple flags (org, repo, period) and fall back to interactive prompts (wizards) when arguments are omitted. This prioritises discoverability and ease of use over scriptability — users are guided through month selection, repo picking, and report generation without memorising flags.

We accept that this makes automated/robotic usage harder. CI pipelines or scripting use cases are a secondary concern; the primary audience is a developer running ad-hoc analysis.
