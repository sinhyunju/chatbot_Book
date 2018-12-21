import argparse

from . import run

__all__ = []

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='worker_manager',
        description='Worker manager to execute a set of worker processes.'
    )
    parser.add_argument('config', help='configuration file (.py)')
    args = parser.parse_args()

    config_locals = {}
    with open(args.config, 'rb') as f:
        code = compile(f.read(), args.config, 'exec')
        exec(code, config_locals)

    if 'worker_config' not in config_locals:
        raise RuntimeError('There is no local variable `worker_config` '
                           'in the configuration file')

    run(config_locals['worker_config'])
