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

ORG_REPOSITORIES_QUERY = gql.gql(
    """
    query FetchOrgRepositories($login: String!, $first: Int!, $after: String) {
        organization(login: $login) {
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
    query FetchRepoMetrics(
        $owner: String!
        $name: String!
        $first: Int!
        $after: String
    ) {
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
                    body
                    commits(last: 20) {
                        nodes {
                            commit {
                                committedDate
                                message
                            }
                        }
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
                    timelineItems(itemTypes: [READY_FOR_REVIEW_EVENT], first: 1) {
                        nodes {
                            ... on ReadyForReviewEvent {
                                createdAt
                            }
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
                    isDraft
                    author {
                        login
                    }
                    reviews(first: 100) {
                        nodes {
                            state
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

SKILL_REPORT_QUERY = gql.gql(
    """
    query SkillReportQuery($query: String!, $first: Int!, $after: String) {
        search(query: $query, type: ISSUE, first: $first, after: $after) {
            nodes {
                ... on PullRequest {
                    number
                    author { login }
                    files(first: 100) {
                        nodes { path additions deletions }
                    }
                }
            }
            pageInfo { hasNextPage endCursor }
        }
    }
    """
)

LANG_REPORT_QUERY = gql.gql(
    """
    query LangReportQuery($query: String!, $first: Int!, $after: String) {
        search(query: $query, type: ISSUE, first: $first, after: $after) {
            nodes {
                ... on PullRequest {
                    number
                    author { login }
                    files(first: 100) {
                        nodes { path additions deletions }
                    }
                }
            }
            pageInfo { hasNextPage endCursor }
        }
    }
    """
)

SEARCH_MERGED_PRS_QUERY = gql.gql(
    """
    query SearchMergedPRs($query: String!, $first: Int!, $after: String) {
        search(query: $query, type: ISSUE, first: $first, after: $after) {
            nodes {
                ... on PullRequest {
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
                    body
                    commits(last: 20) {
                        nodes {
                            commit {
                                committedDate
                                message
                            }
                        }
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
                    timelineItems(itemTypes: [READY_FOR_REVIEW_EVENT], first: 1) {
                        nodes {
                            ... on ReadyForReviewEvent {
                                createdAt
                            }
                        }
                    }
                }
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """
)
