# 
# Note: "make ioctests" output when run in this directory will not be printed
#       to screen until all tests have run unless you unset the MAKEFLAGS
#       environment variable so -Otarget is no longer used
#
#       An easier alternative is to run "make ioctests" in the directory above this
#       instead as this overrides MAKEFLAGS already 
#
ioctests:
	$(PYTHON3) -u run_tests.py
