#!/usr/bin/env python

import sys
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def main():
    file = sys.argv[1]
    api_ref = load(open(file, 'r'), Loader)
    public_endpoints = list(map(lambda kv: kv[0], filter(
        lambda kv: not kv[1].get('x-pd-private', False),
        api_ref['paths'].items()
    )))
    public_endpoints_dict = dict(map(lambda kv: (kv[0], kv[1]), filter(
        lambda kv: not kv[1].get('x-pd-private', False),
        api_ref['paths'].items()
    )))

    print('ENDPOINT_PATTERNS = [')
    for path in public_endpoints:
        print(f"    '{path}',")
    print("]\n")

    print('CURSOR_BASED_ITERATION_ENDPOINTS = [')
    cursor_param_ref = '../common/models/Parameters.yaml#/cursor_cursor'
    for (path, spec) in public_endpoints_dict.items():
        getspec = spec.get('get', {})
        getparams = getspec.get('parameters', [])
        for param in getparams:
            if cursor_param_ref in param.values():
                print(f"    '{path}',")
    print(']')

if __name__ == '__main__':
    main()
