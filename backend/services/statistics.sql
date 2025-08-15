with 
	dates as (
		SELECT generate_series(
    		DATE '2025-08-11',   -- стартовая дата
    		CURRENT_DATE,        -- конечная дата
    		INTERVAL '1 day'     -- шаг
		)::date AS date_day
	),
    users_ctl as (
	select 
		u.id as user_id,
		u.registration_date::date as registration_date_date
	from 
		users u
	where 
		u.id  != '40c4a4e0-1278-42be-bae6-a5a4d4a80805' --Alexandr
		and u.id  != '4176fc9b-3644-471e-9290-a70c627b5247' --Анастасия
		and u.id != '939a46e1-f4e5-47fa-9835-9e86d11800b3' --Denis 
	),
	week_registrations_ctl as (
	select
		wr.id,
		wr.status,
		wr.user_id,
		wr.created_at,
		wr.created_at::date as created_date
	from
		week_registrations wr 
	where
		status = 'active'
		and user_id in (select user_id from users_ctl)
	),
	user_pair_ctl as (
	select
		up.id,
		up.status,
		CASE WHEN up.status = 'pending'   THEN 1 ELSE 0 END AS is_pending,
    	CASE WHEN up.status = 'cancelled' THEN 1 ELSE 0 END AS is_cancelled,
    	CASE WHEN up.status = 'confirmed' THEN 1 ELSE 0 END AS is_confirmed,
    	up.created_at::date as created_date,
    	up.confirmed_at::date as confirmed_date
	from
		user_pairs up
	where
		user1_id in (select user_id from users_ctl)
		or user2_id in (select user_id from users_ctl)
	),
	users_group as (
	select 
		u.registration_date_date as date,
		count(distinct u.user_id) new_users
	from 
		users_ctl u
	group by
		u.registration_date_date	
	),
	week_registrations_group as (
	select 
		wr.created_date as date,
		count(distinct wr.id) week_registrations
	from 
		week_registrations_ctl wr
	group by
		wr.created_date	
	),
	user_pair_group as (
	select 
		up.created_date as date,
		count(distinct up.id) new_pairs,
		sum(up.is_confirmed) confirmed_pairs
	from 
		user_pair_ctl up
	group by
		up.created_date	
	)
	
	select 
		d.date_day,
		u.new_users new_users,
		wr.week_registrations week_registrations,
		up.new_pairs new_pairs,
		up.confirmed_pairs confirmed_pairs
	from dates d
		left join users_group u on d.date_day = u.date
		left join week_registrations_group wr on d.date_day = wr.date
		left join user_pair_group up on d.date_day = up.date