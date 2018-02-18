
# Set these based on your environment.
AC_JAR = ~/AppleUtils/AppleCommander.jar
JACE_JAR = ~/AppleUtils/Jace.jar
TOKENIZER = util/tokenize-asoft

AC = java -jar $(AC_JAR)
JACE = java -jar $(JACE_JAR)  

execute: test_disk
	$(JACE) -computer.s7card mass -s7.d1 basic.po 


# The tokenizer should be able to do a straight compile in Linux.
# Does not require any exotic libraries. May also work under
# other *nix systems, like OS X.
$(TOKENIZER): util/tokenize-asoft.c
	gcc -o $(TOKENIZER) util/tokenize-asoft.c


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

