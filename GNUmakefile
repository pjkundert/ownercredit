
# 
# OnwerCredit GNU 'make' file
# 

PY2=python
PY3=python3

PYTESTOPTS=-v # --capture=no

PY2TEST=$(PY2) -m pytest $(PYTESTOPTS)
PY3TEST=$(PY3) -m pytest $(PYTESTOPTS)

.PHONY: all clean FORCE
all:			help

help:
	@echo  "GNUmakefile for ownercredit.  Targets:"
	@echo  "  test			Run unit tests under Python2"
	@echo  "  install		Install in /usr/local for Python2"
	@echo  "  clean			Remove build artifacts"
	@echo  "  upload		Upload new version to pypi (package maintainer only)"

install:
	$(PY2) setup.py install
	$(PY3) setup.py install

analyze:
	flake8 -j 1 --max-line-length=110					\
	  --ignore=E221,E201,E202,E203,E223,E225,E226,E231,E241,E242,E261,E272,E302,W503,E701,E702,E,W	\
	  --exclude="__init__.py" \
	  .
clean:
	rm -rf build dist auto *.egg-info  $(shell find . -name '*.pyc' -o -name '__pycache__' )

# Support uploading a new version of ownercredit to pypi.  Must:
#   o advance __version__ number in version.py
#   o log in to your pypi account (ie. for package maintainer only)
upload:
	python setup.py sdist upload

# Only run tests in this directory.
test:
	@py.test --version || echo "py.test not found; run 'sudo easy_install pytest'?"
	$(PY2TEST) *_test.py
	$(PY3TEST) *_test.py

# Run only tests with a prefix containing the target string, eg test-blah
test-%:
	$(PY2TEST) *$*_test.py
	$(PY3TEST) *$*_test.py

unit-%:
	$(PY2TEST) -k $*
	$(PY3TEST) -k $*

# 
# Target to allow the printing of 'make' variables, eg:
# 
#     make print-CXXFLAGS
# 
print-%:
	@echo $* = $($*) 
	@echo $*\'s origin is $(origin $*)

