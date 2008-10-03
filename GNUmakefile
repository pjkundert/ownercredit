
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
	rm -rf /tmp/ownercredit-$(VERSION)

ownercredit-$(VERSION).tgz:		/tmp/ownercredit-1.1.0
	tar -C /tmp -czvf $@ ownercredit-1.1.0

ownercredit-$(VERSION).zip:		/tmp/ownercredit-1.1.0
	( cd /tmp && zip -r - $(notdir $<) ) > $@

/tmp/ownercredit-$(VERSION):
	svn export svn+ssh://perry@kundert.ca/home/perry/svn/ownercredit/tags/r$(subst .,_,$(VERSION)) /tmp/ownercredit-$(VERSION)
