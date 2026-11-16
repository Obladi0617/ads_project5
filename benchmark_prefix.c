/* Compile with the same variant macro as huffman.c.
   Input is N followed by N binary strings. Only prefix checking is timed. */
#include <windows.h>
#define main submission_main
#include "huffman.c"
#undef main

int main(void)
{
    int n;
    char codes[MAX_SYMBOLS][MAX_BITS + 1];
    size_t lengths[MAX_SYMBOLS];
    if (scanf("%d", &n) != 1 || n < 2 || n > MAX_SYMBOLS)
        return 1;
    for (int i = 0; i < n; ++i) {
        if (scanf("%63s", codes[i]) != 1)
            return 1;
        lengths[i] = strlen(codes[i]);
    }
    /* A volatile function pointer forces a real call on each iteration. */
    bool (*volatile check)(char (*)[MAX_BITS + 1], const size_t *, int) = prefix_free;
    volatile unsigned accepted = 0;
    const int repeats = 20000;
    for (int i = 0; i < 100; ++i)
        accepted += check(codes, lengths, n);
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&start);
    for (int i = 0; i < repeats; ++i)
        accepted += check(codes, lengths, n);
    QueryPerformanceCounter(&end);
    double nanoseconds = (double)(end.QuadPart - start.QuadPart) * 1e9 / frequency.QuadPart / repeats;
    printf("%.3f %u\n", nanoseconds, accepted);
    return 0;
}

