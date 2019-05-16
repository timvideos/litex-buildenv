#!/usr/bin/env python3
import sys
inv_filter = None
if len(sys.argv) > 1:
    inv_filter = sys.argv[-1]

import urllib.request

import conf
for url, data in conf.intersphinx_mapping.values():
    inv_file = data[-1]
    if inv_filter and inv_file != inv_filter:
        continue
    full_url = url + 'objects.inv'

    print('Downloading '+full_url+' -> '+inv_file)
    urllib.request.urlretrieve(full_url, inv_file)
