
# 
# GNU 'make' file
# 

VERSION		:=2.0.0
OWFSVER		:=2.8p2
OWFSPTH		:=http://sourceforge.net/projects/owfs/files/owfs/$(OWFSVER)/owfs-$(OWFSVER).tar.gz

.PHONY: all clean
all:				ownercredit-$(VERSION).zip	\
				ownercredit-$(VERSION).tgz	\
				clean
clean:
	rm -rf /tmp/ownercredit-$(VERSION)			\
	    *.pyc 						\
	    owfs-$(OWFSVER)*

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
# 
# lander.py	-- A partially complete Lunar Lander, with PID "auto" mode (spacebar switches)
# hydronic.py	-- Core of a thermodynamic simulation for hydronically heated structures
# jesperse.py	-- An thermodynamic simulation of an actual residence
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
								\
					lander.py		\
					hydronic.py		\
					hydronic_test.py	\
					jespersen.py
	rsync -va $^ $@/


# 
# Various tools used in Hydronic system implementations
# 
# ow, owfs -- Dallas Semiconductor 1-wire I/O
.PHONY: owfs ow
owfs:				/opt/owfs/bin/owserver
ow:				/usr/lib/python2.6/dist-packages/ow

/opt/owfs/bin/owserver:		owfs-$(OWFSVER)
	cd $<; ./configure && make # && make install
/usr/lib/python2.6/dist-packages/ow:				\
				owfs-$(OWFSVER)
	cd $</modules/swig/python && python setup.py install
owfs-$(OWFSVER):		owfs-$(OWFSVER).tar.gz
	tar xzf $<
owfs-$(OWFSVER).tar.gz:
	wget -c $(OWFSPTH)

