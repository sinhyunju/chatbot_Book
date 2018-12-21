import os
import sys
import traceback


def _read_config_file(config_path):
    config_path_from_env = os.getenv('CONFIG_PATH')
    if config_path_from_env is not None:
        print('Replace config path with environment variable.', file=sys.stderr)
        config_path = config_path_from_env

    try:
        with open(config_path, encoding='utf-8') as f:
            config_source = f.read()
    except FileNotFoundError:
        print('Cannot find config file at "%s".' % config_path, file=sys.stderr)
        sys.exit(1)

    try:
        config_module_variables = dict()
        exec(config_source, config_module_variables)
    except Exception:
        traceback.print_exc()
        print('Failed to evaluate config file.', file=sys.stderr)
        sys.exit(1)

    config = dict()
    for k, v in config_module_variables.items():
        if not k.startswith('_') and k.isupper():
            config[k] = v

    return config


class _ConfigProxy:
    def __init__(self, config_dict):
        self._config_dict = config_dict

    def items(self):
        return self._config_dict.items()

    def get(self, key, d=None):
        return self._config_dict.get(key, d)

    def ensure(self, key):
        if key not in self._config_dict:
            raise KeyError('Configuration key "%s" is missing!' % key)

    def extract(self, *keys):
        # TODO : return `_FrozenConfigProxy` and implement compile-time validation
        for key in keys:
            self.ensure(key)
        return _ConfigProxy({key: self._config_dict[key] for key in keys})

    def __getattr__(self, key):
        return self._config_dict[key]

    def __getitem__(self, key):
        return self._config_dict[key]


def load_config(config_path='configs/default.py'):
    return _ConfigProxy(_read_config_file(config_path))
