# Restaurant Monitor API

## Project Overview
The Restaurant Monitor API is a FastAPI-based service designed to monitor the status of restaurant stores. It provides accurate uptime and downtime metrics by properly extrapolating store status observations within defined business hours and timezones. The API supports generating detailed reports on store performance over various time intervals.


## API Endpoints
- **POST /trigger_report**  
  Triggers the generation of a comprehensive uptime/downtime report for all stores. The report generation runs as a background task and returns a unique report ID.

- **GET /get_report?report_id=**  
  Retrieves the status of a report by its ID. If the report is complete, it returns the report as a downloadable CSV file. Otherwise, it returns the current status.

- **GET /health**  
  Returns a simple health check response with the current timestamp.

## Uptime/Downtime Calculation Logic

The core logic for computing uptime and downtime is implemented in `calculator.py`. It involves the following key steps:

1. **Business Hours Overlap Calculation**  
   The function `get_business_intervals` computes the intervals that overlap with the store's defined business hours within a given time range. It converts timestamps to the store's timezone and ensures only the hours falling inside business hours are considered for uptime/downtime calculations.

2. **Extrapolation of Status Observations**  
   The function `extrapolate_for_interval` analyzes the store's status observations within each business interval. It calculates the total uptime and downtime in minutes by considering the status changes over time. If no observations exist for a segment, it assumes the previous known status or defaults to active.

    - For each business interval:
    - Gather all polling observations within the interval.
    - **Forward-fill** status:  
    - The status at each poll is assumed to persist until the next poll or the end of the interval.
    - For the period before the first poll in the interval, use the last known status **before** the interval (even if from a previous day).  
    - If no previous status exists, default to "active" (configurable).
    - For each segment between polls (or between interval boundaries and polls), calculate the duration as uptime or downtime based on the status.

3. **Overall Uptime/Downtime Calculation**  
   The function `calculate_uptime_downtime` aggregates the uptime and downtime across all business intervals for a store within the specified time range. It returns the total uptime, downtime, total business minutes, and the count of observations used.

This logic ensures accurate and meaningful uptime/downtime metrics by respecting business hours and handling gaps in observation data.

## Report Generation

The report generation process is handled in `report.py`. It performs the following:

- Determines the current time based on the latest observation timestamp.
- Defines time intervals for the last hour, day, and week.
- Fetches store observations, business hours, and timezones from the database.
- Uses the uptime/downtime calculation logic to compute metrics for each store over the defined intervals.
- Compiles the results into a CSV report containing uptime and downtime for each store.
- Saves the report status and CSV data in the database for retrieval via the API.

## Setup and Running

To run the API server:

1. Ensure dependencies are installed (see `requirements.txt`).
2. Add env variables for database connection.
3. Start the FastAPI server by running:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Use the API endpoints to trigger and retrieve reports.

**Kindly refer to the sample output file provided in the repository for reference.**

---
## Ideas to Improve the Solution

To further enhance the scalability, reliability, and performance of this system, consider the following improvements:

### 1. Parallel Processing per Store

- **Description:**  
  Uptime/downtime calculations for each store are independent and can be processed in parallel. By leveraging Python’s multiprocessing, threading, or distributed task queues (such as Celery or RQ), you can divide the workload among multiple CPU cores or machines.
- **Benefit:**  
  Significantly reduces total report generation time and enables the system to scale efficiently as the number of stores increases.

### 2. Kafka for Real-Time Data Ingestion

- **Description:**  
  Integrate Apache Kafka as a real-time streaming platform to ingest and buffer polling data. Kafka can decouple data producers from consumers, handle high-throughput event ingestion, and provide durability with replayability.
- **Benefit:**  
  Enables the system to process millions of events per second, supports real-time analytics and alerting, and increases reliability and scalability for high-frequency data environments.

### 3. Database Sharding

- **Description:**  
  As the dataset grows, consider sharding (partitioning) the database by store ID, time range, or other relevant criteria. This distributes data across multiple database servers or partitions.
- **Benefit:**  
  Improves query performance, reduces single-node bottlenecks, and allows the system to scale horizontally to handle very large datasets and high query loads.

---

**Implementing these improvements will make the system production-ready for enterprise-scale deployments and future growth.**



