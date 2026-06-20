class InfluxRepository:
    def __init__(self, client):
        self.client = client

    def query(self, sql):
        return self.client.query(sql)

    def write(self, line_protocol):
        return self.client.write(line_protocol)

    @staticmethod
    def escape_string(string):
        return string.translate(
            string.maketrans({",": r"\,", " ": r"\ ", "=": r"\="})
        )

    @staticmethod
    def extract_single_value(result):
        series = result["results"][0].get("series", [])

        if not series:
            return None

        values = series[0].get("values", [])

        if not values:
            return None

        return values[0][1]
