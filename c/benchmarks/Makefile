CC = gcc
CFLAGS = -std=c99 -O2 -Wall -I../include
LIBRARY_FLAGS_MAC = -L../lib/Darwin -lsdd -lm
LIBRARY_FLAGS_LINUX = -L../lib/Linux -lsdd -lm

all: modelCountingMac

modelCountingLinux: src/doModelCount.o
	$(CC) $(CFLAGS) $^ $(LIBRARY_FLAGS_LINUX) -o "doModelCounting"

modelCountingMac: src/doModelCount.o
	$(CC) $(CFLAGS) $^ $(LIBRARY_FLAGS_MAC) -o "doModelCounting"


clean:
	rm -f src/*.o test-* circuit circuit-gc output/*.dot output/*.png output/*.sdd
