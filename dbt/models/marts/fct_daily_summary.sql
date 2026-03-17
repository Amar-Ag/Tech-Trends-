{{ config(materialized='incremental') }}

with stg as (
    select * from {{ ref('stg_github_events') }}  
    {% if is_incremental() %}
    -- only runs on incremental runs, not the first run
    where event_date > (
        select max(event_date) from {{ this }}
    )
    {% endif %}
)

select
    event_date,
    event_type,
    COUNT(*) as event_count
from stg
where event_date is not null
group by event_date, event_type
order by event_date desc