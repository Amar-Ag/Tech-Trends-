/* @bruin
name: prod.fct_daily_summary
type: bq.sql
materialization:
  type: table
  strategy: merge
depends:
  - prod.stg_github_events
columns:
  - name: event_date
    type: DATE
    primary_key: true
  - name: event_type
    type: STRING
    primary_key: true
  - name: event_count
    type: INTEGER
@bruin */

with stg as (
    select * from `tech-trends-489801.prod.stg_github_events`  
)
select
    event_date,
    event_type,
    COUNT(*) as event_count
from stg
where event_date is not null
group by event_date, event_type
order by event_date desc