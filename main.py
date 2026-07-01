from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
import os
import yaml

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

def to_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "on"}

def coerce_value(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)

def normalize_env_key(env_key):
    if env_key == "NUM_WORKERS":
        return "workers"
    if env_key.startswith("APP_"):
        return env_key[4:].lower()
    return env_key.lower()

def read_yaml_layer(env_name="development"):
    filename = f"config.{env_name}.yaml"
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k: coerce_value(k, v) for k, v in data.items()}

def read_dotenv_layer():
    data = dotenv_values(".env")
    result = {}
    for k, v in data.items():
        if v is None:
            continue
        key = normalize_env_key(k)
        result[key] = coerce_value(key, v)
    return result

def read_os_env_layer():
    result = {}
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            key = normalize_env_key(k)
            result[key] = coerce_value(key, v)
    return result

def parse_cli_overrides(set_params):
    result = {}
    for item in set_params:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        result[key] = coerce_value(key, value)
    return result

@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()
    config.update(read_yaml_layer("development"))
    config.update(read_dotenv_layer())
    config.update(read_os_env_layer())
    config.update(parse_cli_overrides(set))

    masked = config.copy()
    masked["api_key"] = "****"
    return masked
