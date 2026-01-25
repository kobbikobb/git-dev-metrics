from .reports import get_all_repositories, get_pull_request_metrics


class GitHubClient:
    def __init__(self, token: str, org: str, repo: str):
        self.token = token
        self.org = org
        self.repo = repo

    def get_all_repos(self):
        return get_all_repositories(self.token)

    def get_development_metrics(self, period: str):
        return get_pull_request_metrics(self.token, self.org, self.repo, period)
