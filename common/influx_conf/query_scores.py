from influxdb_client import InfluxDBClient
from common.influx_conf.influx_config import INFLUX_BUCKET, INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)

def query_latest_table(bucket: str, measurement: str, camera: str, operator: str):
    query_api = client.query_api()
    query = f'''
        from(bucket: "{bucket}")
          |> range(start: -5m)
          |> filter(fn: (r) => r._measurement == "{measurement}")
          |> filter(fn: (r) => r["camera"] == "{camera}")
          |> filter(fn: (r) => r["operator"] == "user_{operator}")
          |> last()
    '''
    result = query_api.query(org=INFLUX_ORG, query=query)
    print(query)

    values = {}
    for table in result:
        for record in table.records:
            key = record.values.get("label") or record.get_field()
            values[key] = record.get_value()
    return values
