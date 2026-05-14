# File-based reports over web application

Reports are generated as static HTML files (dashboard, trend, stale) opened in the browser. No web server, no routing, no state management.

This avoids the operational complexity of hosting a web app (deployment, auth, persistence). A web application is a viable future direction if the tool grows beyond single-user analysis, but for now static files deliver the same information with zero infrastructure.
