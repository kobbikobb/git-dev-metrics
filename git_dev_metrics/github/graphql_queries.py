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

PULL_REQUESTS_QUERY = gql.gql(
    """
    query FetchPullRequests($owner: String!, $name: String!, $first: Int!, $after: String) {
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

REVIEWS_QUERY = gql.gql(
    """
    query FetchReviews($owner: String!, $name: String!, $first: Int!, $after: String) {
        repository(owner: $owner, name: $name) {
            pullRequests(
                first: $first
                after: $after
                states: MERGED
                orderBy: {field: UPDATED_AT, direction: DESC}
            ) {
                nodes {
                    number
                    mergedAt
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
