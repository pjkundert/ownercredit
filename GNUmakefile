
# 
# OnwerCredit GNU 'make' file
# 

VERSION		:=3.0.0

.PHONY: all clean
all:				ownercredit-$(VERSION).zip	\
				ownercredit-$(VERSION).tgz	\
				clean
clean:
	rm -rf /tmp/ownercredit-$(VERSION)			\
	    *.pyc

# Only run tests in this directory.
test:
	@py.test --version || echo "py.test not found; run 'sudo easy_install pytest'?"
	py.test --capture=no *_test.py

# Run only tests with a prefix containing the target string, eg test-filtered
test-%:
	py.test --capture=no *$*_test.py

# 
# Target to allow the printing of 'make' variables, eg:
# 
#     make print-CXXFLAGS
# 
print-%:
	@echo $* = $($*) 
	@echo $*\'s origin is $(origin $*)

# 
# Owner Credit implemention
# 
# credit.py	-- A model wealth-backed currency implementation
# pid.py	-- A PID controller implementation
# misc.py	-- Various math related utilites, such as NaN, and a generic "value" type object
# filtered.py	-- Things that act like numerical values, but implement averaging type behaviour
# lander.py	-- A partially complete Lunar Lander, with PID "auto" mode (spacebar switches)
# 
ownercredit-$(VERSION).tgz:		/tmp/ownercredit-$(VERSION)
	tar -C /tmp -czvf $@ ownercredit-$(VERSION)

ownercredit-$(VERSION).zip:		/tmp/ownercredit-$(VERSION)
	( cd /tmp && zip -r - $(notdir $<) ) > $@

/tmp/ownercredit-$(VERSION):		README			\
					GNUmakefile		\
					credit.py		\
					credit_test.py		\
					pid.py			\
					pid_test.py		\
					misc.py			\
					misc_test.py		\
					filtered.py		\
					filtered_test.py	\
					lander.py

	rsync -va $^ $@/

