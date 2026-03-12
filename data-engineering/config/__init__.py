import os
import yaml
from pathlib import Path

_config_path = Path(__file__).parent / "config.yaml"

with open(_config_path, "r", encoding="utf-8") as f:
    settings = yaml.safe_load(f)


def _resolve_env_vars(d):
    for k, v in d.items():
        if isinstance(v, dict):
            _resolve_env_vars(v)
        elif isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            if env_var in os.environ:
                d[k] = os.environ[env_var]


_resolve_env_vars(settings)
