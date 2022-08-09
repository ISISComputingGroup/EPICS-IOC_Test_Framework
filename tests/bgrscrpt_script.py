import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.environ["KIT_ROOT"], "ISIS", "inst_servers", "master")))

from server_common.helpers import register_ioc_start

register_ioc_start("BGRSCRPT_01")
print("IOC started")

# This script creates a temporary directory so we can test if execution from path macro was successful in bgrscrpt.py 
os.mkdir("BGRSCRPT_01_test_dir")
