try:
    import yaml  # type: ignore[import-not-found]
except ModuleNotFoundError:
    yaml = None


def load_config(config_path):
    if yaml is None:
        raise ModuleNotFoundError(
            "PyYAML is required to load YAML configuration files. "
            "Install it with: pip install pyyaml"
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Invalid configuration file")

    return config




