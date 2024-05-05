CFLAGS += -g -O3 -no-pie

all:
	$(CC) $(CFLAGS) -I./include -L./ -Wl,--whole-archive -lm5 -Wl,--no-whole-archive -o main main.c
