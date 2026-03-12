with stg as (
    select * from {{ ref('stg_github_events') }}
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