import pyodbc
import json

def get_connection(database:str):
    with open("config.json") as f:
        config = json.load(f)

    db_conf = config["database"]
    conn_str = (
        f"DRIVER={db_conf['driver']};"
        f"SERVER={db_conf['server']};"
        f"DATABASE={database};"
        f"UID={db_conf['user']};"
        f"PWD={db_conf['password']}"
    )
    return pyodbc.connect(conn_str)
