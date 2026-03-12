import os
import re
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_ENV_PATTERN = re.compile(r"\$\{([^:}]+)(?::([^}]*))?\}")


def _resolve_env_vars(value):
    if not isinstance(value, str):
        return value

    def replace_match(match):
        var_name = match.group(1)
        default = match.group(2) if match.group(2) is not None else ""
        return os.getenv(var_name, default)

    return _ENV_PATTERN.sub(replace_match, value)


def _process_config(obj):
    if isinstance(obj, dict):
        return {k: _process_config(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_process_config(i) for i in obj]
    else:
        return _resolve_env_vars(obj)


_config_path = Path(__file__).parent / "config.yaml"
with open(_config_path) as f:
    _raw = yaml.safe_load(f)

settings = _process_config(_raw)
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
