import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pytz
from models import StatusObservation, BusinessHour, UptimeDowntimeResult

logger = logging.getLogger(__name__)

def get_business_intervals(start_time: datetime, end_time: datetime,
                            business_hours: Dict[int, BusinessHour],
                            timezone_str: str) -> List[Tuple[datetime, datetime]]:
    """
    The get_business_intervals() function is designed to include only the hours that fall 
    inside the store’s business hours, and remove extra hours outside of that.
    """
    logger.info(f"Calculating business intervals from {start_time} to {end_time} for timezone {timezone_str}")

    if not business_hours:
        return [(start_time, end_time)]

    tz = pytz.timezone(timezone_str)
    intervals = []

    local_start = start_time.replace(tzinfo=pytz.UTC).astimezone(tz)
    local_end = end_time.replace(tzinfo=pytz.UTC).astimezone(tz)

    current_date = local_start.date()
    end_date = local_end.date()

    while current_date <= end_date:
        day_of_week = current_date.weekday()

        if day_of_week in business_hours:
            bh = business_hours[day_of_week]

            business_start_local = tz.localize(datetime.combine(current_date, bh.start_time))
            business_end_local = tz.localize(datetime.combine(current_date, bh.end_time))

            if bh.end_time < bh.start_time:
                business_end_local += timedelta(days=1)

            business_start_utc = business_start_local.astimezone(pytz.UTC).replace(tzinfo=None)
            business_end_utc = business_end_local.astimezone(pytz.UTC).replace(tzinfo=None)

            interval_start = max(business_start_utc, start_time)
            interval_end = min(business_end_utc, end_time)

            if interval_start < interval_end:
                intervals.append((interval_start, interval_end))

        current_date += timedelta(days=1)

    logger.info(f"Calculated {len(intervals)} business intervals")
    return intervals

def extrapolate_for_interval(interval_start: datetime, interval_end: datetime,
                             observations: List[StatusObservation]) -> UptimeDowntimeResult:
    
    relevant_obs = [obs for obs in observations if interval_start <= obs.timestamp_utc <= interval_end]
    relevant_obs.sort(key=lambda x: x.timestamp_utc)

    total_interval_minutes = (interval_end - interval_start).total_seconds() / 60
    uptime_minutes = 0.0
    downtime_minutes = 0.0

    if not relevant_obs:
        uptime_minutes = total_interval_minutes
        return UptimeDowntimeResult(uptime_minutes, downtime_minutes, total_interval_minutes, 0)

    previous_obs = [obs for obs in observations if obs.timestamp_utc < interval_start]
    assumed_status = previous_obs[-1].status if previous_obs else relevant_obs[0].status

    first_segment_duration = (relevant_obs[0].timestamp_utc - interval_start).total_seconds() / 60
    if first_segment_duration > 0:
        if assumed_status == 'active':
            uptime_minutes += first_segment_duration
        else:
            downtime_minutes += first_segment_duration

    current_time = relevant_obs[0].timestamp_utc
    for i in range(1, len(relevant_obs)):
        obs = relevant_obs[i]
        segment_duration = (obs.timestamp_utc - current_time).total_seconds() / 60
        prev_status = relevant_obs[i-1].status
        if segment_duration > 0:
            if prev_status == 'active':
                uptime_minutes += segment_duration
            else:
                downtime_minutes += segment_duration
        current_time = obs.timestamp_utc

    final_segment_duration = (interval_end - current_time).total_seconds() / 60
    if final_segment_duration > 0:
        final_status = relevant_obs[-1].status
        if final_status == 'active':
            uptime_minutes += final_segment_duration
        else:
            downtime_minutes += final_segment_duration

    logger.info(f"Extrapolated interval {interval_start} to {interval_end}: uptime {uptime_minutes} mins, downtime {downtime_minutes} mins, observations {len(relevant_obs)}")
    return UptimeDowntimeResult(uptime_minutes, downtime_minutes, total_interval_minutes, len(relevant_obs))

def calculate_uptime_downtime(store_id: str,
                               start_time: datetime,
                               end_time: datetime,
                               store_observations: List[StatusObservation],
                               business_hours: Dict[int, BusinessHour],
                               timezone_str: str) -> UptimeDowntimeResult:
    logger.info(f"Calculating uptime/downtime for store {store_id} from {start_time} to {end_time}")
    #store_observations = [obs for obs in observations if obs.store_id == store_id]

    business_intervals = get_business_intervals(start_time, end_time, business_hours, timezone_str)

    total_uptime = 0.0
    total_downtime = 0.0
    total_business_time = 0.0
    total_observations = 0

    for interval_start, interval_end in business_intervals:
        result = extrapolate_for_interval(interval_start, interval_end, store_observations)
        total_uptime += result.uptime_minutes
        total_downtime += result.downtime_minutes
        total_business_time += result.total_business_minutes
        total_observations += result.observations_count

    logger.info(f"Calculated uptime/downtime for store {store_id}: uptime {total_uptime} mins, downtime {total_downtime} mins, total business time {total_business_time} mins, observations {total_observations}")
    return UptimeDowntimeResult(total_uptime, total_downtime, total_business_time, total_observations)
