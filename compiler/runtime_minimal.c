/*
 * Maxx Minimal Runtime (Level 1 bootstrap) - implementation.
 *
 * A tiny, dependency-free runtime: malloc-backed strings, a print function,
 * channels, file IO, and time. This exists only to run bootstrap programs;
 * the production runtime (GC, scheduler, real IO) is a Level 2+ concern.
 */
#define _POSIX_C_SOURCE 200809L
#include "runtime_minimal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <unistd.h>

/* ------------------------------------------------------------------ */
/* Strings                                                             */
/* ------------------------------------------------------------------ */

mx_str mx_str_lit(const char* s) {
    mx_str r;
    r.ptr = s;
    r.len = (int64_t)strlen(s);
    return r;
}

mx_str mx_str_concat(mx_str a, mx_str b) {
    size_t total = (size_t)a.len + (size_t)b.len;
    char* buf = (char*)malloc(total + 1);
    if (!buf) {
        fprintf(stderr, "mx_str_concat: out of memory\n");
        abort();
    }
    memcpy(buf, a.ptr, (size_t)a.len);
    memcpy(buf + a.len, b.ptr, (size_t)b.len);
    buf[total] = '\0';
    mx_str r;
    r.ptr = buf;
    r.len = (int64_t)total;
    return r;
}

void mx_println(mx_str s) {
    fwrite(s.ptr, 1, (size_t)s.len, stdout);
    fputc('\n', stdout);
}

void mx_print(mx_str s) {
    fwrite(s.ptr, 1, (size_t)s.len, stdout);
}

mx_str mx_int_to_str(int64_t v) {
    char buf[32];
    int n = snprintf(buf, sizeof(buf), "%lld", (long long)v);
    char* out = (char*)malloc((size_t)n + 1);
    memcpy(out, buf, (size_t)n + 1);
    mx_str r;
    r.ptr = out;
    r.len = n;
    return r;
}

mx_str mx_double_to_str(double v) {
    char buf[64];
    int n = snprintf(buf, sizeof(buf), "%g", v);
    char* out = (char*)malloc((size_t)n + 1);
    memcpy(out, buf, (size_t)n + 1);
    mx_str r;
    r.ptr = out;
    r.len = n;
    return r;
}

mx_str mx_bool_to_str(bool v) {
    if (v) return mx_str_lit("true");
    return mx_str_lit("false");
}

/* ------------------------------------------------------------------ */
/* IO                                                                  */
/* ------------------------------------------------------------------ */

mx_str mx_read_line(void) {
    char* buf = NULL;
    size_t cap = 0;
    ssize_t n = getline(&buf, &cap, stdin);
    if (n < 0) {
        free(buf);
        return mx_str_lit("");
    }
    /* Strip trailing newline. */
    while (n > 0 && (buf[n-1] == '\n' || buf[n-1] == '\r')) {
        buf[--n] = '\0';
    }
    mx_str r;
    r.ptr = buf;
    r.len = n;
    return r;
}

mx_str mx_read_file(mx_str path) {
    FILE* f = fopen(path.ptr, "rb");
    if (!f) return mx_str_lit("");
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = (char*)malloc((size_t)sz + 1);
    fread(buf, 1, (size_t)sz, f);
    buf[sz] = '\0';
    fclose(f);
    mx_str r;
    r.ptr = buf;
    r.len = sz;
    return r;
}

int64_t mx_write_file(mx_str path, mx_str content) {
    FILE* f = fopen(path.ptr, "wb");
    if (!f) return -1;
    size_t n = fwrite(content.ptr, 1, (size_t)content.len, f);
    fclose(f);
    return (int64_t)n;
}

/* ------------------------------------------------------------------ */
/* Time                                                                */
/* ------------------------------------------------------------------ */

double mx_now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

void mx_sleep(double secs) {
    struct timespec ts;
    ts.tv_sec = (time_t)secs;
    ts.tv_nsec = (long)((secs - (double)ts.tv_sec) * 1e9);
    nanosleep(&ts, NULL);
}

/* ------------------------------------------------------------------ */
/* Channel stub (single-threaded, bounded ring buffer).                */
/* ------------------------------------------------------------------ */

struct mx_chan_str {
    mx_str buf[64];
    int head;
    int tail;
};

mx_chan_str* mx_chan_str_new(void) {
    mx_chan_str* ch = (mx_chan_str*)calloc(1, sizeof(mx_chan_str));
    return ch;
}

void mx_chan_str_send(mx_chan_str* ch, mx_str s) {
    ch->buf[ch->tail] = s;
    ch->tail++;
}

mx_str mx_chan_str_recv(mx_chan_str* ch) {
    mx_str s = ch->buf[ch->head];
    ch->head++;
    return s;
}
