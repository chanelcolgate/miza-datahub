from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from miza_datahub.postgres.postgres_repository import PostgresRepository


class ElectricityConsumptionQuery(PostgresRepository):
    """
    Query class for electricity consumption data analysis from PostgreSQL.
    Uses SQLAlchemy with psycopg[binary] driver.
    """

    def get_daily_consumption_by_timestamp(
        self, start_timestamp: int, end_timestamp: int
    ) -> List[Dict[str, Any]]:
        """
        Get daily electricity consumption grouped by device.

        Args:
            start_timestamp: Start timestamp in milliseconds
            end_timestamp: End timestamp in milliseconds

        Returns:
            List of dictionaries containing production_day,
            device_name, total_consumption
        """
        sql = """
            SELECT
                to_char(
                    (DATE((to_timestamp(h.ts / 1000) - INTERVAL '6 hours')
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                        + INTERVAL '6 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) / 1000 AS total_consumption
            FROM hourly_electricity_consumption h
            JOIN device d ON h.entity_id = d.id
            WHERE
                h.ts >= :start_timestamp
                AND h.ts <= :end_timestamp
            GROUP BY
                1, d.id, 2
            ORDER BY
                1 ASC,
                3 DESC
        """
        params = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        return self.query(sql, params)

    def get_daily_consumption_by_device(
        self, date_str: str
    ) -> List[Dict[str, Any]]:
        """
        Get electricity consumption for a specific date grouped by device.

        Retrieves all consumption records for a single day
        in Asia/Ho_Chi_Minh timezone.

        Args:
            date_str: Date string in format 'YYYY-MM-DD' (e.g., '2026-06-21')

        Returns:
            List of dictionaries with keys:
                - production_day: Date in Asia/Ho_Chi_Minh timezone
                - device_name: Device name from device table
                - total_consumption: Total consumption for the device on
                this day
        """
        # Parse date and calculate timestamps from 06:00 AM
        # current day to 06:00 AM next day
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        # Start: 06:00 AM on the given date
        day_start = date_obj.replace(hour=6, minute=0, second=0, microsecond=0)
        # End: 06:00 AM on the next day
        day_end = day_start + timedelta(days=1)

        # Convert to milliseconds
        start_timestamp = int(day_start.timestamp() * 1000)
        end_timestamp = int(day_end.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    (date_trunc('day', to_timestamp(h.ts / 1000 - 21600)
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                        + INTERVAL '6 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) / 1000 AS total_consumption
            FROM hourly_electricity_consumption h
            JOIN device d ON h.entity_id = d.id
            WHERE
                h.ts >= :start_timestamp
                AND h.ts < :end_timestamp
            GROUP BY
                1, d.id, 2
            ORDER BY
                1 ASC;
        """
        params = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        return self.query(sql, params)

    def get_daily_consumption_by_shift(
        self, date_str: str, shift: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query class for electiricity consumption data analysis from PostgreSQL.

        Uses SQLAlchemy with psycopg[binary] driver.
        Provides methods to query and insert electricity consumption data.

        Note: All time periods are aligned to 06:00 (6 AM)
        in Asia/Ho_Chi_Minh timezone.

        Shift definitions (Asia/Ho_Chi_Minh timezone):
        - Shift 1: 06:00 - 14:00 (morning shift)
        - Shift 2: 14:00 - 22:00 (afternoon shift)
        - Shift 3: 22:00 - 06:00 (night shift, spans two calendar days)

        Args:
            date_str: Date string in format 'YYYY-MM-DD' (e.g., '2026-06-21')
            shift: Shift number (1, 2, 3) or None for full day. Default is None.

        Returns:
            List of dictionaries with keys:
                - production_hour: Hour timestamp formatted
                    as 'YYYY-MM-DD HH:MM:SS'
                - device_name: Device name from device table
                - total_consumption: Total consumption in kWh for this hour
        """

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        if shift is None:
            # Full day: 06:00 AM current day to 06:00 AM next day
            start_time = date_obj.replace(
                hour=6, minute=0, second=0, microsecond=0
            )
            end_time = start_time + timedelta(days=1)
        elif shift == 1:
            start_time = date_obj.replace(
                hour=6, minute=0, second=0, microsecond=0
            )
            end_time = date_obj.replace(
                hour=14, minute=0, second=0, microsecond=0
            )
        elif shift == 2:
            start_time = date_obj.replace(
                hour=14, minute=0, second=0, microsecond=0
            )
            end_time = date_obj.replace(
                hour=22, minute=0, second=0, microsecond=0
            )
        elif shift == 3:
            start_time = date_obj.replace(
                hour=22, minute=0, second=0, microsecond=0
            )
            end_time = (date_obj + timedelta(days=1)).replace(
                hour=5, minute=0, second=0, microsecond=0
            )
        else:
            raise ValueError(
                f"Invalid shift number: {shift}. Must be 1, 2, 3, or None."
            )
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    date_trunc('hour', to_timestamp(h.ts / 1000)
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'),
                    'YYYY-MM-DD HH24:MI:SS'
                ) AS production_hour,
                d.name AS device_name,
                SUM(h.e_consumption) / 1000 AS total_consumption
            FROM hourly_electricity_consumption h
            JOIN device d ON h.entity_id = d.id
            WHERE
                h.ts >= :start_timestamp
                AND h.ts <= :end_timestamp
            GROUP BY
                date_trunc('hour', to_timestamp(h.ts / 1000)
                    AT TIME ZONE 'Asia/Ho_Chi_Minh') ,
                d.id,
                d.name
            ORDER BY
                1 ASC;
        """
        params = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        return self.query(sql, params)

    def get_montly_consumption_by_device(
        self, month: int, year: int
    ) -> List[Dict[str, Any]]:
        """
        Get monthly electricity consumption grouped by device

        Retrieves consumption data from 06:00 AM on the first day of the month
        to 06:00 AM on the first day of the next month
        in Asia/Ho_Chi_Minh timezone.

        Args:
            month: Month number (1-12)
            year: Year (e.g., 2026)

        Returns:
            List of dictionaries with keys:
                - production_day: Date in Asia/Ho_Chi_Minh timezone
                - device_name: Device name from device table
                - total_consumption: Total consumption in kWh
        """
        # Start: 06:00 AM on the first day of the given month
        month_start = datetime(year, month, 1, hour=6, minute=0, second=0)

        # End: 06:00 AM on the first day of the next month
        if month == 12:
            month_end = datetime(year + 1, 1, 1, hour=6, minute=0, second=0)
        else:
            month_end = datetime(year, month + 1, 1, hour=5, minute=0, second=0)

        # Convert to milliseconds
        start_timestamp = int(month_start.timestamp() * 1000)
        end_timestamp = int(month_end.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    (date_trunc('month', to_timestamp(h.ts / 1000 - 21600)
                    AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                    + INTERVAL '6 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) / 1000 AS total_consumption
            FROM hourly_electricity_consumption h
            JOIN device d ON h.entity_id = d.id
            WHERE
                h.ts >= :start_timestamp
                AND h.ts < :end_timestamp
                AND d.name = 'Meter XLNT 2'
            GROUP BY
                1, d.id, 2
            ORDER BY
                1 ASC
        """
        params = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        return self.query(sql, params)

    def get_yearly_consumption_by_device(
        self, year: int
    ) -> List[Dict[str, Any]]:
        """
        Get yearly electricity consumption grouped by device.

        Retrieves consumption data from 06:00 AM on January 1st to 06:00 AM on
        January 1st of the next year in Asia/Ho_Chi_Minh timezone.

        Args:
            year: Year (e.g., 2026)

        Returns:
            List of dictionaries with keys:
                - production_day: Date in Asia/Ho_Chi_Minh timezone
                - device_name: Device name from device table
                - total_consumption: Total consumption in kWh
        """
        # Start: 06:00 AM on January 1st of the given year
        year_start = datetime(year, 1, 1, hour=6, minute=0, second=0)
        # End: 06:00 AM on January 1st of the next year
        year_end = datetime(year + 1, 1, 1, hour=6, minute=0, second=0)

        # Convert to milliseconds
        start_timestamp = int(year_start.timestamp() * 1000)
        end_timestamp = int(year_end.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    (date_trunc('year', to_timestamp(h.ts / 1000 - 21600)
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                        + INTERVAL '6 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) / 1000 AS total_consumption
            FROM hourly_electricity_consumption h
            JOIN device d ON h.entity_id = d.id
            WHERE
                h.ts >= :start_timestamp
                AND h.ts < :end_timestamp
            GROUP BY
                1, d.id, 2
            ORDER BY
                1 ASC
        """
        params = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        return self.query(sql, params)
