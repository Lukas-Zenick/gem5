#!/bin/bash
mkdir ../mnt
cd util/m5
# cp ../../uintr-measure/micro/uintr-ipc-bench/source/m5/src/SConscript src/SConscript
scons build/x86/out/m5
cp build/x86/out/libm5.a ../../test-source/.
cp src/m5_mmap.h ../../test-source/.
mkdir ../../test-source/include
cp -a ../../include ../../test-source/
cd ../../
