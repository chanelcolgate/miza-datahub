import logging

from miza_datahub.postgres.postgres_repository import PostgresRepository

logger = logging.getLogger(__name__)


class PlanProductionAnalyzerWriter(PostgresRepository):
    def write_data(self, df):
        df = df.reset_index()
        df["start_time"] = df["start_time"].dt.strftime("%Y-%m-%d %H:%M:%S%z")

        data_to_insert = df.to_dict(orient="records")

        insert_sql = """
            INSERT INTO paper_production (
                start_time,
                paper_grade,
                customer,
                gsm_target,
                production_total,
                speed_target,
                production_total_per_hour,
                duration
            ) VALUES (
                :start_time,
                :paper_grade,
                :customer,
                :gsm_target,
                :production_total,
                :speed_target,
                :production_total_per_hour,
                :duration
            );
        """

        try:
            if self.get_health():
                logger.info(
                    f"Preparing to insert {len(data_to_insert)}"
                    " records into TimescaleDB..."
                )

                affected_rows = self.execute_many(
                    sql=insert_sql, data=data_to_insert
                )

                logger.info(
                    "Completed! Successfully inserted "
                    f"{affected_rows} rows of data."
                )
            else:
                logger.error(
                    "Failed to connect to the database. "
                    "Please check your DB_CONFIG."
                )
        except Exception as e:
            logger.error(f"Data processing or insertion failed: {e}")
        finally:
            self.dispose()
