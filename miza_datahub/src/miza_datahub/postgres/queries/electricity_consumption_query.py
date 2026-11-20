from typing import List, Dict, Any, Optional

from miza_datahub.services import shift_calendar
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
                    (DATE((to_timestamp(h.ts / 1000) - INTERVAL '7 hours')
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                        + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) AS total_consumption
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
        day_start, day_end = shift_calendar.production_day_range(date_str)
        start_timestamp = int(day_start.timestamp() * 1000)
        end_timestamp = int(day_end.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    (date_trunc('day', to_timestamp(h.ts / 1000 - 25200)
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                        + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) AS total_consumption
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

        Note: All time periods are aligned to 07:00 (7 AM)
        in Asia/Ho_Chi_Minh timezone.

        Shift definitions (Asia/Ho_Chi_Minh timezone):
        - Shift 1: 07:00 - 19:00 (day shift)
        - Shift 2: 19:00 - 07:00 (night shift, spans two calendar days)

        Args:
            date_str: Date string in format 'YYYY-MM-DD' (e.g., '2026-06-21')
            shift: Shift number (1, 2) or None for full day. Default is None.

        Returns:
            List of dictionaries with keys:
                - production_hour: Hour timestamp formatted
                    as 'YYYY-MM-DD HH:MM:SS'
                - device_name: Device name from device table
                - total_consumption: Total consumption in kWh for this hour
        """

        start_time, end_time = shift_calendar.shift_window(date_str, shift)
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    date_trunc('hour', to_timestamp(h.ts / 1000)
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'),
                    'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) AS total_consumption
            FROM hourly_electricity_consumption h
            JOIN device d ON h.entity_id = d.id
            WHERE
                h.ts >= :start_timestamp
                AND h.ts < :end_timestamp
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

    def get_monthly_consumption_by_device(
        self, month: int, year: int
    ) -> List[Dict[str, Any]]:
        """
        Get monthly electricity consumption grouped by device

        Retrieves consumption data from 07:00 AM on the first day of the month
        to 07:00 AM on the first day of the next month
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
        month_start, month_end = shift_calendar.production_month_range(
            year, month
        )
        start_timestamp = int(month_start.timestamp() * 1000)
        end_timestamp = int(month_end.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    (date_trunc('month', to_timestamp(h.ts / 1000 - 25200)
                    AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                    + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) AS total_consumption
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

    def get_yearly_consumption_by_device(
        self, year: int
    ) -> List[Dict[str, Any]]:
        """
        Get yearly electricity consumption grouped by device.

        Retrieves consumption data from 07:00 AM on January 1st to 07:00 AM on
        January 1st of the next year in Asia/Ho_Chi_Minh timezone.

        Args:
            year: Year (e.g., 2026)

        Returns:
            List of dictionaries with keys:
                - production_day: Date in Asia/Ho_Chi_Minh timezone
                - device_name: Device name from device table
                - total_consumption: Total consumption in kWh
        """
        year_start, year_end = shift_calendar.production_year_range(year)
        start_timestamp = int(year_start.timestamp() * 1000)
        end_timestamp = int(year_end.timestamp() * 1000)

        sql = """
            SELECT
                to_char(
                    (date_trunc('year', to_timestamp(h.ts / 1000 - 25200)
                        AT TIME ZONE 'Asia/Ho_Chi_Minh'))
                        + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS'
                ) AS production_day,
                d.name AS device_name,
                SUM(h.e_consumption) AS total_consumption
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
