
# 
# GNU 'make' file
# 
# .tgz 	-- tar and gzipped file
# .zip 	-- zip file
# 
#     Both contain a version-numbered directory, which contains the files
# 
VERSION		:=1.1.0
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



# Only run tests in this directory.
test:
	py.test --capture=no *_test.py

ownercredit-$(VERSION).tgz:		/tmp/ownercredit-$(VERSION)
	tar -C /tmp -czvf $@ ownercredit-$(VERSION)

ownercredit-$(VERSION).zip:		/tmp/ownercredit-$(VERSION)
	( cd /tmp && zip -r - $(notdir $<) ) > $@

/tmp/ownercredit-$(VERSION):
	svn export svn+ssh://perry@kundert.ca/home/perry/svn/ownercredit/tags/r$(subst .,_,$(VERSION)) /tmp/ownercredit-$(VERSION)
