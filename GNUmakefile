
# 
# GNU 'make' file
# 
# .tgz 	-- tar and gzipped file
# .zip 	-- zip file
# 
#     Both contain a version-numbered directory, which contains the files
# 
VERSION		:= 1.1.0

.PHONY: all clean
all:				ownercredit-$(VERSION).zip	\
				ownercredit-$(VERSION).tgz	\
				clean
clean:
	rm -rf /tmp/ownercredit-$(VERSION) *.pyc

test:
	py.test --nocapture --nomagic

ownercredit-$(VERSION).tgz:		/tmp/ownercredit-$(VERSION)
	tar -C /tmp -czvf $@ ownercredit-$(VERSION)

ownercredit-$(VERSION).zip:		/tmp/ownercredit-$(VERSION)
	( cd /tmp && zip -r - $(notdir $<) ) > $@

/tmp/ownercredit-$(VERSION):
	svn export svn+ssh://perry@kundert.ca/home/perry/svn/ownercredit/tags/r$(subst .,_,$(VERSION)) /tmp/ownercredit-$(VERSION)
