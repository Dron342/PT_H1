LEADERBOARD_QUERY = """query LeaderboardSample(
  $year: Int!
  $quarter: Int
  $first: Int
  $key: LeaderboardKeyEnum!
  $filter: String
  $user_type: String
) {
  leaderboard_entries(
    key: $key
    year: $year
    quarter: $quarter
    first: $first
    filter: $filter
    user_type: $user_type
  ) {
    edges {
      node {
        ... on __TYPE_NAME__ {
          id
          rank
          previous_rank
          __METRIC_FIELDS__
          user {
            id
            username
            profile_picture(size: medium)
            mark_as_company_on_leaderboards
          }
        }
      }
    }
  }
}"""


PROFILE_QUERY = """query UserProfilePageQuery($resourceIdentifier: String!) {
  user(username: $resourceIdentifier) {
    id
    username
    name
    intro
    profile_activated
    created_at
    location
    website
    bio
    bugcrowd_handle
    hack_the_box_handle
    github_handle
    gitlab_handle
    linkedin_handle
    twitter_handle
    cleared
    verified
    open_for_employment
    mark_as_company_on_leaderboards
    reputation
    user_streak {
      id
      length
      start_date
      end_date
    }
    submitted_reports: reports(where: {state: {_neq: draft}}) {
      total_count
    }
    resolved_report_counts {
      id
      valid_vulnerability_count
      severity_low_count
      severity_medium_count
      severity_high_count
      severity_critical_count
    }
    statistics_snapshot(snapshot_type: past_year) {
      id
      signal
      impact
    }
  }
}"""


HACKTIVITY_QUERY = """query HacktivitySearchQuery(
  $queryString: String!
  $from: Int
  $size: Int
  $sort: SortInput!
) {
  search(
    index: CompleteHacktivityReportIndex
    query_string: $queryString
    from: $from
    size: $size
    sort: $sort
  ) {
    total_count
    nodes {
      __typename
      ... on HacktivityDocument {
        id
        _id
        reporter {
          id
          username
          name
        }
        cve_ids
        cwe
        severity_rating
        public
        report {
          id
          databaseId: _id
          title
          substate
          url
          disclosed_at
          report_generated_content {
            id
            hacktivity_summary
          }
        }
        votes
        team {
          id
          handle
          name
          url
          currency
        }
        total_awarded_amount
        latest_disclosable_action
        latest_disclosable_activity_at
        submitted_at
        disclosed
        has_collaboration
        collaborators {
          id
          username
          name
        }
      }
    }
  }
}"""
