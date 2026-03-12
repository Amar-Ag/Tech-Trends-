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
        
        -- created_at is now a proper TIMESTAMP — no conversion needed
        DATE(created_at) as event_date,
        EXTRACT(HOUR FROM created_at) as event_hour,
        created_at

    from source
)

select * from renamed