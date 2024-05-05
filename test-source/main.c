
#include <stdio.h>

#include <gem5/m5ops.h>

#include "m5_mmap.h"

int main()
{
    m5op_addr = 0xFFFF0000;
    map_m5_mem();
    printf("Hello world\n");
    m5_switch_cpu_addr();
    while (1)
        ;
    m5_exit_addr(0);
}
