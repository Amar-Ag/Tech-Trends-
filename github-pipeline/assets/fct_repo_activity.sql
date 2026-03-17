/* @bruin
name: prod.fct_repo_activity
type: bq.sql
materialization:
  type: table
depends:
  - prod.stg_github_events
@bruin */

with stg as (
    select * from `tech-trends-489801.prod.stg_github_events`  
)
select
    repo_name,
    repo_owner,
    repo_slug,
    COUNT(*) as total_events,
    COUNTIF(event_type = 'WatchEvent') as star_count,     
    COUNTIF(event_type = 'ForkEvent') as fork_count,
    COUNTIF(event_type = 'PushEvent') as push_count,
    MIN(event_date) as first_seen,
    MAX(event_date) as last_seen
from stg
where repo_name is not null
    and repo_name != ''
group by repo_name, repo_owner, repo_slug
order by total_events desc