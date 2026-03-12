-- stg_github_events.sql
-- Cleans and standardises raw GitHub events

with source as (
    select * from {{ source('raw', 'github_events') }}
),

renamed as (
    select
        -- identifiers
        event_id,
        event_type,
        
        -- actor (person who did the action)
        actor_login,
        actor_id,
        
        -- repository
        repo_name,
        repo_owner,
        repo_slug,
        
        -- created_at is stored as nanoseconds — divide by 1000 to get microseconds
        DATE(TIMESTAMP_MICROS(CAST(created_at / 1000 AS INT64)))              as event_date,
        EXTRACT(HOUR FROM TIMESTAMP_MICROS(CAST(created_at / 1000 AS INT64))) as event_hour,
        TIMESTAMP_MICROS(CAST(created_at / 1000 AS INT64))                    as created_at

    from source
)

select * from renamed