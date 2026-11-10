#include <stdbool.h>
#include <stdio.h>
#include <string.h>

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

#ifdef PAIRWISE
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
typedef struct {
    int children[2];
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
        weights[(unsigned char)symbol] = weight;
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
            lengths[i] = strlen(codes[i]);
            if (weights[key] < 0 || seen[key] ||
                strspn(codes[i], "01") != lengths[i]) {
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
