# Maxx Machine Code Bootstrap
# ============================
# 纯 x86_64 机器码，不依赖任何高级语言。

all: boot0 maxxc-stage1.bin

boot0: boot0.o
	ld -o boot0 boot0.o -e _start

boot0.o: boot0.s
	as --64 boot0.s -o boot0.o

maxxc-stage1.bin: stage1.o
	ld -o maxxc-stage1.bin stage1.o --oformat binary -e _start -Ttext=0x10000000

stage1.o: stage1.s
	as --64 stage1.s -o stage1.o

clean:
	rm -f *.o boot0 maxxc-stage1.bin

test: boot0 maxxc-stage1.bin
	./boot0

.PHONY: all clean test
