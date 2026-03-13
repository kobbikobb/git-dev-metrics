import gql

REPOSITORIES_QUERY = gql.gql(
    """
    query FetchRepositories($first: Int!, $after: String) {
        viewer {
            repositories(
                first: $first
                after: $after
                orderBy: {field: PUSHED_AT, direction: DESC}
            ) {
                nodes {
                    nameWithOwner
                    isPrivate
                    pushedAt
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """
)

REPO_METRICS_QUERY = gql.gql(
    """
    query FetchRepoMetrics($owner: String!, $name: String!, $first: Int!, $after: String) {
        repository(owner: $owner, name: $name) {
            pullRequests(
                first: $first
                after: $after
                states: MERGED
                orderBy: {field: UPDATED_AT, direction: DESC}
            ) {
                nodes {
                    number
                    title
                    createdAt
                    mergedAt
                    additions
                    deletions
                    changedFiles
                    author {
                        login
                    }
                    commits(first: 1) {
                        nodes {
                            commit {
                                committedDate
                            }
                        }
                    }
                    # Note: max 100 reviews per PR - truncates if more
                    reviews(first: 100) {
                        nodes {
                            author {
                                login
                            }
                            state
                            submittedAt
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """
)

OPEN_PRS_QUERY = gql.gql(
    """
    query FetchOpenPRs($owner: String!, $name: String!, $first: Int!, $after: String) {
        repository(owner: $owner, name: $name) {
            pullRequests(
                first: $first
                after: $after
                states: OPEN
                orderBy: {field: CREATED_AT, direction: DESC}
            ) {
                nodes {
                    number
                    title
                    createdAt
                    author {
                        login
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """
)
