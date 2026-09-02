from typing import Any, Dict
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from jekyll_writer.config import ConfigManager
from jekyll_writer.publisher import PublisherEngine

app = FastAPI(title="Jekyll Writer Web", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_config_manager() -> ConfigManager:
    return ConfigManager()


def _sanitize_config(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k != "ssh_password"}


@app.get("/api/config")
def get_config(cfg: ConfigManager = Depends(get_config_manager)) -> Dict[str, Any]:
    return _sanitize_config(cfg.data)


@app.post("/api/config")
def save_config(
    payload: Dict[str, Any],
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    allowed_keys = [
        "jekyll_root",
        "jekyll_command",
        "ssh_host",
        "ssh_port",
        "ssh_user",
        "ssh_remote_path",
    ]
    for key in allowed_keys:
        if key in payload:
            cfg.set(key, payload[key])

    # Never persist ssh_password
    cfg.set("ssh_password", "")
    cfg.save()
    return _sanitize_config(cfg.data)


@app.post("/api/config/clear-cache")
def clear_cache(
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    root = cfg.get("jekyll_root", "")
    engine = PublisherEngine()
    engine.clear_sync_cache(root)
    return {"success": True, "message": "Cache limpo com sucesso!"}
