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
    def calculate_pq(actual, plan, df_quality):
        df_actual = OEEService.production_dataframe(actual, "actual")
        df_plan = OEEService.production_dataframe(plan, "plan")

        if not df_quality is None:
            df_quality = pd.DataFrame(columns=["production_day", "B"])

        df_final = df_actual.merge(
            df_quality[["production_day", "B"]],
            on="production_day",
            how="outer",
        ).merge(df_plan, on="production_day", how="left")

        if df_final.empty:
            return pd.DataFrame(
                columns=["production_day", "actual", "plan", "B", "P", "Q"]
            )

        df_final["P"] = (df_final["actual"] / df_final["plan"] * 100).round(2)
        df_final["Q"] = (
            (df_final["actual"] - df_final["B"] / 1000)
            / df_final["actual"]
            * 100
        ).round(2)
        df_final = df_final.replace([np.inf, -np.inf], np.nan)
        df_final = df_final.astype(object)
        df_final = df_final.where(pd.notnull(df_final), None)
        return df_final
