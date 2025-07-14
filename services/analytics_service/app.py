from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.influx_conf.query_scores import query_latest_table
from src.influx_conf.influx_config import INFLUX_BUCKET

app = FastAPI(title="Analytics Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/reba/{camera_id}/{operator}")
def api_get_reba_table(camera_id: int, operator: str):
    camera_tag = f"camera_{camera_id}"
    data = query_latest_table(bucket=INFLUX_BUCKET, measurement="reba_table", camera=camera_tag, operator=operator)
    if not data:
        raise HTTPException(status_code=404, detail="Dados REBA não encontrados")
    return {"camera": camera_tag, "operator": operator, "reba_table": data}

@app.get("/rula/{camera_id}/{operator}")
def api_get_rula_table(camera_id: int, operator: str):
    camera_tag = f"camera_{camera_id}"
    data = query_latest_table(bucket=INFLUX_BUCKET, measurement="rula_table", camera=camera_tag, operator=operator)
    if not data:
        raise HTTPException(status_code=404, detail="Dados RULA não encontrados")
    return {"camera": camera_tag, "operator": operator, "rula_table": data}
