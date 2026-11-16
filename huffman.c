#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>

enum { MAX_SYMBOLS = 63, MAX_BITS = 63, MAX_NODES = 1 + MAX_SYMBOLS * MAX_BITS };

typedef struct {
    int values[MAX_SYMBOLS];
    int size;
} MinHeap;

static void push(MinHeap *heap, int weight)
{
    int i = heap->size++;
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (heap->values[parent] <= weight)
            break;
        heap->values[i] = heap->values[parent];
        i = parent;
    }
    heap->values[i] = weight;
}

static int pop(MinHeap *heap)
{
    int minimum = heap->values[0];
    int last = heap->values[--heap->size];
    int i = 0;
    while (2 * i + 1 < heap->size) {
        int child = 2 * i + 1;
        if (child + 1 < heap->size && heap->values[child + 1] < heap->values[child])
            ++child;
        if (last <= heap->values[child])
            break;
        heap->values[i] = heap->values[child];
        i = child;
    }
    heap->values[i] = last;
    return minimum;
}

static int optimal_cost(MinHeap *heap)
{
    int cost = 0;
    /* A merge pushes every leaf in the merged subtree one level deeper. */
    while (heap->size > 1) {
        int weight = pop(heap);
        weight += pop(heap);
        cost += weight;
        push(heap, weight);
    }
    return cost;
}

#if defined(INTERVAL) || defined(SORTED) || defined(PACKED)
typedef struct {
    uint64_t start;
    uint64_t end;
} CodeInterval;

#if defined(INTERVAL)
static int compare_intervals(const void *left, const void *right)
{
    const CodeInterval *a = left;
    const CodeInterval *b = right;
    return (a->start > b->start) - (a->start < b->start);
}
#endif

static bool prefix_free(char codes[][MAX_BITS + 1], const size_t lengths[], int n)
{
    CodeInterval intervals[MAX_SYMBOLS];
    for (int i = 0; i < n; ++i) {
        uint64_t value = 0;
        for (size_t j = 0; j < lengths[i]; ++j)
            value = (value << 1) | (uint64_t)(codes[i][j] - '0');
        unsigned shift = MAX_BITS - (unsigned)lengths[i];
        CodeInterval current;
        current.start = value << shift;
        /* The exclusive endpoint can equal 2^63, which fits in uint64_t. */
        current.end = (value + UINT64_C(1)) << shift;
#if defined(SORTED)
        /* Keep disjoint intervals sorted while inserting; only neighbors can overlap. */
        int position = i;
        while (position > 0 && intervals[position - 1].start > current.start) {
            intervals[position] = intervals[position - 1];
            --position;
        }
        if ((position > 0 && current.start < intervals[position - 1].end) ||
            (position < i && intervals[position].start < current.end))
            return false;
        intervals[position] = current;
#elif defined(PACKED)
        /* Compare intervals with fixed-width operations rather than string scans. */
        for (int j = 0; j < i; ++j) {
            if (current.start < intervals[j].end && intervals[j].start < current.end)
                return false;
        }
        intervals[i] = current;
#else
        intervals[i] = current;
#endif
    }
#if defined(INTERVAL)
    qsort(intervals, (size_t)n, sizeof intervals[0], compare_intervals);
    for (int i = 1; i < n; ++i) {
        if (intervals[i].start < intervals[i - 1].end)
            return false;
    }
#endif
    return true;
}
#elif defined(PAIRWISE)
/* Experimental baseline. Equality also counts as a prefix conflict. */
static bool prefix_free(char codes[][MAX_BITS + 1], const size_t lengths[], int n)
{
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            size_t shorter = lengths[i] < lengths[j] ? lengths[i] : lengths[j];
            if (memcmp(codes[i], codes[j], shorter) == 0)
                return false;
        }
    }
    return true;
}
#else
/* At most 3970 nodes; 16-bit child indices reduce the working set. */
typedef struct {
    uint16_t children[2];
    bool terminal;
} TrieNode;

static bool prefix_free(char codes[][MAX_BITS + 1], const size_t lengths[], int n)
{
    TrieNode trie[MAX_NODES];
    int used = 1;
    trie[0] = (TrieNode){0};

    for (int i = 0; i < n; ++i) {
        int node = 0;
        for (size_t j = 0; j < lengths[i]; ++j) {
            /* A previously inserted code ends before this one does. */
            if (trie[node].terminal)
                return false;
            int bit = codes[i][j] - '0';
            if (trie[node].children[bit] == 0) {
                trie[node].children[bit] = used;
                trie[used++] = (TrieNode){0};
            }
            node = trie[node].children[bit];
        }
        /* An equal code already exists, or this code prefixes an earlier one. */
        if (trie[node].terminal || trie[node].children[0] || trie[node].children[1])
            return false;
        trie[node].terminal = true;
    }
    return true;
}
#endif

int main(void)
{
    int n;
    if (scanf("%d", &n) != 1 || n < 2 || n > MAX_SYMBOLS)
        return 1;

    /* Index by symbol rather than relying on the order of a submission. */
    int weights[256];
    for (int i = 0; i < 256; ++i)
        weights[i] = -1;

    MinHeap heap = {0};
    for (int i = 0; i < n; ++i) {
        char symbol;
        int weight;
        if (scanf(" %c %d", &symbol, &weight) != 2 || weight < 0 || weight > 1000)
            return 1;
        unsigned char key = (unsigned char)symbol;
        if (weights[key] >= 0)
            return 1;
        weights[key] = weight;
        push(&heap, weight);
    }
    int optimum = optimal_cost(&heap);

    int submissions;
    if (scanf("%d", &submissions) != 1)
        return 1;
    for (int entry = 0; entry < submissions; ++entry) {
        bool seen[256] = {false};
        char codes[MAX_SYMBOLS][MAX_BITS + 1];
        size_t lengths[MAX_SYMBOLS];
        bool valid = true;
        int cost = 0;

        /* Consume all N rows even if one is invalid, to stay aligned with the next entry. */
        for (int i = 0; i < n; ++i) {
            char symbol;
            if (scanf(" %c %63s", &symbol, codes[i]) != 2)
                return 1;
            unsigned char key = (unsigned char)symbol;
            /* strspn yields the full length exactly when the token is binary. */
            lengths[i] = strspn(codes[i], "01");
            if (weights[key] < 0 || seen[key] ||
                codes[i][lengths[i]] != '\0') {
                valid = false;
            } else {
                cost += weights[key] * (int)lengths[i];
                seen[key] = true;
            }
        }

        /* The exact bit pattern can differ from any particular Huffman tree. */
        puts(valid && cost == optimum && prefix_free(codes, lengths, n) ? "Yes" : "No");
    }
    return 0;
}
