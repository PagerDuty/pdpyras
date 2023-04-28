#!/usr/bin/env python

# This script is not part of the pdpyras library. Rather, it can be used for the
# by PagerDuty engineers to assist the development and maintenance of pdpyras.
# It automatically generates the declaration of module variables
# "ENDPOINT_PATTERNS" and "CURSOR_BASED_ITERATION_ENDPOINTS" from the API
# documentation source code (which is kept in a private repository in the
# PagerDuty GitHub org).
#
# To use, run this script with its sole argument a path to
# "reference/v2/Index.yaml" inside a clone of the repo:

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

    print('CANONICAL_PATHS = [')
    for path in public_endpoints:
        print(f"    '{path}',")
    print("]")
    print('"""'+"\nExplicit list of supported canonical REST API v2 paths")
    print("\n:meta hide-value:\n"+'"""'+"\n")

    print('CURSOR_BASED_PAGINATION_PATHS = [')
    cursor_param_ref = '../common/models/Parameters.yaml#/cursor_cursor'
    for (path, spec) in public_endpoints_dict.items():
        getspec = spec.get('get', {})
        getparams = getspec.get('parameters', [])
        for param in getparams:
            if cursor_param_ref in param.values():
                print(f"    '{path}',")
    print(']')
    print('"""'+"\nExplicit list of paths that support cursor-based pagination")
    print("\n:meta hide-value:\n"+'"""')


if __name__ == '__main__':
    main()
