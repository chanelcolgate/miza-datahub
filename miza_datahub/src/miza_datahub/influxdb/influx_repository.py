class InfluxRepository:
    def __init__(self, client):
        self.client = client

    def query(self, sql):
        return self.client.query(sql)

    def write(self, line_protocol):
        return self.client.write(line_protocol)
