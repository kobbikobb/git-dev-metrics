# File-based reports over web application

## Problem

Needed a way to deliver reports (dashboard, trend, stale PRs) without operating infrastructure.

## Options

Web application (deferred — adds auth, deployment, persistence, routing overhead). Static HTML files (chosen).

## Solution

Generate static HTML files and open them in the browser. No web server, no routing, no state management. Jinja2 templates render the snapshot data directly to HTML.

## Consequences

No hosting infrastructure needed. Limited to single-user read-only reports. A web application is a viable future direction if the tool grows beyond individual analysis.
