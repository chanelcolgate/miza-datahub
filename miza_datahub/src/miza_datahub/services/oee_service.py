import pandas as pd
import numpy as np


class OEEService:
    @staticmethod
    def production_dataframe(data: list, value_column: str) -> pd.DataFrame:
        if not data:
            return pd.DataFrame(columns=["production_day", value_column])
        df = pd.DataFrame(data, columns=["time", value_column])
        df["production_day"] = (
            pd.to_datetime(df["time"]).dt.tz_localize(None).dt.normalize()
        )
        return df[["production_day", value_column]]

    @staticmethod
    def calculate_pq(actual, plan, df_quality, mode: str = "PQ"):
        """
        Calculates OEE metrics based on the specified mode.
        :param mode: 'P' to calculate Performance,
                     'Q' to calculate Quality,
                     'PQ' to calculate Performance and Quality
        """
        df_actual = OEEService.production_dataframe(actual, "actual")
        df_plan = OEEService.production_dataframe(plan, "plan")

        if df_quality is not None:
            df_quality = pd.DataFrame(columns=["production_day", "B"])

        df_final = df_actual.merge(
            df_quality[["production_day", "B"]],
            on="production_day",
            how="outer",
        ).merge(df_plan, on="production_day", how="left")

        if df_final.empty:
            base_cols = ["production_day", "actual", "plan", "B"]
            if "P" in mode.upper():
                base_cols.append("P")
            if "Q" in mode.upper():
                base_cols.append("Q")
            return pd.DataFrame(columns=base_cols)

        mode_upper = mode.upper()

        if "P" in mode_upper:
            df_final["P"] = (df_final["actual"] / df_final["plan"]).round(4)

        if "Q" in mode_upper:
            df_final["Q"] = (
                (df_final["actual"] - df_final["B"] / 1000) / df_final["actual"]
            ).round(4)

        df_final = df_final.replace([np.inf, -np.inf], np.nan)
        df_final = df_final.astype(object)
        df_final = df_final.where(pd.notnull(df_final), None)

        output_columns = ["production_day", "actual", "plan", "B"]
        if "P" in mode_upper:
            output_columns.append("P")
        if "Q" in mode_upper:
            output_columns.append("Q")
        return df_final[output_columns]

    @staticmethod
    def merge_metrics_to_dict_list(
        availability_res, performance_res, last_speed_res
    ):
        try:
            avail_values = availability_res.get("values", [[]])[0]
            time_target = avail_values[0] if len(avail_values) > 0 else "N/A"
            avail_a = avail_values[1] if len(avail_values) > 1 else None

            perf_values = performance_res.get("values", [[]])[0]
            actual = perf_values[1] if len(perf_values) > 1 else None
            target = perf_values[2] if len(perf_values) > 2 else None
            perf_p = perf_values[3] if len(perf_values) > 3 else None

            speed_values = last_speed_res.get("values", [[]])[0]
            reel_speed = speed_values[1] if len(speed_values) > 1 else None
            wire_speed = speed_values[2] if len(speed_values) > 2 else None
            moisture = speed_values[3] if len(speed_values) > 3 else None

            quality_q = 98.0
            oee = (avail_a * perf_p * quality_q) / 10000.0

            merged_data = {
                "time": time_target,
                "A": avail_a,
                "P": perf_p,
                "Q": quality_q,
                "OEE": round(oee, 2),
                "actual": actual,
                "target": target,
                "reel_speed": reel_speed,
                "wire_speed": wire_speed,
                "moisture": moisture,
            }

            return [merged_data]
        except (IndexError, TypeError, KeyError) as e:
            print(f"Error when merging data: {e}")
            return []
