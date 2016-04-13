#!/usr/bin/env python
# -*- coding: utf-8 -*-
from index_service import IndexService
import sys


def main():
    args = read_config()
    index_service = IndexService(**args)

def read_config():
    try:
        with open('config.txt', 'r') as f:
            d = eval(f.read())
        return d
    except:
        raise IOError("config.txt not present")

if __name__ == "__main__":  
    main()
