#!/bin/bash

scons build/X86_MESI_Two_Level/gem5.opt -j$(nproc) --linker=mold
