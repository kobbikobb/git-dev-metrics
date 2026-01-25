from .queries import run_query

class GitHubClient:

    def __init__(self, org: str, repo: str):
        self.org = org
        self.repo = repo

    def get_development_metrics(self, period: str):
        return run_query(self.org, self.repo, period)
