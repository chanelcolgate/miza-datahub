import requests


class InfluxRestClient:
    def __init__(self, host: str, port: int, database: str):
        self.database = database
        self.query_url = f"http://{host}:{port}/query"
        self.write_url = f"http://{host}:{port}/write"

    def query(self, sql: str):
        response = requests.get(
            self.query_url, params={"db": self.database, "q": sql}
        )

        response.raise_for_status()
        return response.json()

    def write(self, payload: str):
        response = requests.post(
            self.write_url,
            params={"db": self.database, "presision": "s"},
            data=payload,
        )

        response.raise_for_status()
        return response.text
