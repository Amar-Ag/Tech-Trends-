with stg as (
    select * from {{ ref('stg_github_events') }}  
)

select
    event_date,
    event_type,
    COUNT(*) as event_count
from stg
where event_date is not null
group by event_date, event_type
order by event_date desc