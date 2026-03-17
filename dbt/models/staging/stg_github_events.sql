{{ config(materialized='incremental') }}

with source as (
    select * from {{ source('raw', 'github_events') }}
    
    {% if is_incremental() %}
    -- only runs on incremental runs, not the first run
    where created_at > (
        select max(created_at) from {{ this }}
    )
    {% endif %}
),

renamed as (
    select
        event_id,
        event_type,
        actor_login,
        actor_id,
        repo_name,
        repo_owner,
        repo_slug,
        DATE(created_at)              as event_date,
        EXTRACT(HOUR FROM created_at) as event_hour,
        created_at
    from source
)

select * from renamed