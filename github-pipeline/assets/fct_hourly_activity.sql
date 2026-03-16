/* @bruin
name: prod.fct_hourly_activity
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
    event_hour as hour_of_day,
    COUNT(*) as event_count,
    COUNTIF(event_type = 'PushEvent') as push_count,
    COUNTIF(event_type = 'WatchEvent') as star_count
from stg
where event_hour is not null
group by event_hour
order by hour_of_day