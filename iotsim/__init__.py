"""
python lib for IoT Simulator project
"""

import os

PKG_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def read_from(path):
    with open(os.path.join(PKG_ROOT_DIR, path)) as f:
        return f.read().strip()

__version__ = read_from('VERSION.txt')