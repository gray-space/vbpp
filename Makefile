
# Set these based on your environment.
AC_JAR = ~/AppleUtils/AppleCommander.jar
JACE_JAR = ~/AppleUtils/Jace.jar
TOKENIZER = bt
AC = ac
#
EMULATOR = sa2

execute: test_disk
	$(JACE) -computer.s7card mass -s7.d1 basic.po 



TEST_SOURCES = tests/test.baz tests/functest.baz tests/longiftest.baz \
	      tests/asserttest.baz tests/looptest.baz tests/example.baz 
TEST_OBJECTS = $(TEST_SOURCES:.baz=.bas)
TEST_BINS = $(TEST_OBJECTS:.bas=.bin)

.PRECIOUS: %.bas

%.bas:  %.baz 
	python baz-to-bas.py  --outfile $@ $<

%.bin:  %.bas $(TOKENIZER)
	$(TOKENIZER) $< $@

test_disk: $(TEST_BINS)
	cp disk_images/blank.po basic.po
	for X in $(TEST_BINS); do \
		echo $$X; \
		echo `basename $$X | cut -f 1 -d '.'`; \
		echo $(AC) -p basic.po `basename $$X | cut -f 1 -d '.'` bas 0x0801 < $$X; \
		$(AC) -p basic.po `basename $$X | cut -f 1 -d '.'` bas 0x0801 < $$X; \
	done
	
	

.PHONY: clean
clean:
	rm basic.po *.bas *.bin tests/*.bas tests/*.bin DemoApps/*.bas DemoApps/*.bin || true

