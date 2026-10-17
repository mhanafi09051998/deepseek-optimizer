"""Resolve application configuration from defaults, file, environment, args."""

import argparse
import json
import os

DEFAULTS = {"host": "localhost", "port": 8000, "debug": False}


def load(overrides=None, env=None):
    env = os.environ if env is None else env
    config = dict(DEFAULTS)

    if "APP_HOST" in env:
        config["host"] = env["APP_HOST"]
    if "APP_PORT" in env:
        config["port"] = int(env["APP_PORT"])
    if "APP_DEBUG" in env:
        config["debug"] = env["APP_DEBUG"].lower() in ("1", "true", "yes")

    path = env.get("APP_CONFIG")
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            config.update(json.load(handle))

    overrides = overrides or {}
    for key in ("host", "port", "debug"):
        value = overrides.get(key)
        if value is not None:
            config[key] = value
    return config


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--debug", action="store_true", default=None)
    args = parser.parse_args(argv)
    overrides = {"host": args.host, "port": args.port, "debug": args.debug}
    print(json.dumps(load(overrides), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
