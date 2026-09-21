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

bool mx_str_eq(mx_str a, mx_str b) {
    if (a.len != b.len) return false;
    return memcmp(a.ptr, b.ptr, (size_t)a.len) == 0;
}

bool mx_str_lt(mx_str a, mx_str b) {
    size_t min_len = (size_t)(a.len < b.len ? a.len : b.len);
    int cmp = memcmp(a.ptr, b.ptr, min_len);
    if (cmp != 0) return cmp < 0;
    return a.len < b.len;
}

bool mx_str_gt(mx_str a, mx_str b) {
    return mx_str_lt(b, a);
}

/* String manipulation functions. */
mx_str mx_str_upper(mx_str s) {
    char* buf = (char*)malloc((size_t)s.len + 1);
    memcpy(buf, s.ptr, (size_t)s.len);
    buf[s.len] = '\0';
    for (int64_t i = 0; i < s.len; i++) {
        if (buf[i] >= 'a' && buf[i] <= 'z') buf[i] -= 32;
    }
    mx_str r = {buf, s.len};
    return r;
}

mx_str mx_str_lower(mx_str s) {
    char* buf = (char*)malloc((size_t)s.len + 1);
    memcpy(buf, s.ptr, (size_t)s.len);
    buf[s.len] = '\0';
    for (int64_t i = 0; i < s.len; i++) {
        if (buf[i] >= 'A' && buf[i] <= 'Z') buf[i] += 32;
    }
    mx_str r = {buf, s.len};
    return r;
}

mx_str mx_str_trim(mx_str s) {
    int64_t start = 0, end = s.len;
    while (start < end && (s.ptr[start] == ' ' || s.ptr[start] == '\t' || s.ptr[start] == '\n')) start++;
    while (end > start && (s.ptr[end-1] == ' ' || s.ptr[end-1] == '\t' || s.ptr[end-1] == '\n')) end--;
    char* buf = (char*)malloc((size_t)(end - start) + 1);
    memcpy(buf, s.ptr + start, (size_t)(end - start));
    buf[end - start] = '\0';
    mx_str r = {buf, end - start};
    return r;
}

mx_str mx_str_substr(mx_str s, int64_t start, int64_t len) {
    if (start < 0) start = 0;
    if (start > s.len) start = s.len;
    if (len < 0) len = 0;
    if (start + len > s.len) len = s.len - start;
    char* buf = (char*)malloc((size_t)len + 1);
    memcpy(buf, s.ptr + start, (size_t)len);
    buf[len] = '\0';
    mx_str r = {buf, len};
    return r;
}

int64_t mx_str_find(mx_str s, mx_str pat) {
    if (pat.len == 0) return 0;
    for (int64_t i = 0; i <= s.len - pat.len; i++) {
        if (memcmp(s.ptr + i, pat.ptr, (size_t)pat.len) == 0) return i;
    }
    return -1;
}

mx_str mx_str_char_at(mx_str s, int64_t idx) {
    if (idx < 0 || idx >= s.len) return mx_str_lit("");
    char c[2] = {s.ptr[idx], '\0'};
    return mx_str_lit(c);
}

mx_str mx_str_replace(mx_str s, mx_str from, mx_str to) {
    int64_t pos = mx_str_find(s, from);
    if (pos < 0) return s;
    mx_str before = mx_str_substr(s, 0, pos);
    mx_str after = mx_str_substr(s, pos + from.len, s.len - pos - from.len);
    mx_str result = mx_str_concat(before, to);
    result = mx_str_concat(result, after);
    return result;
}

int64_t mx_parse_int(mx_str s) {
    return atoll(s.ptr);
}

double mx_parse_float(mx_str s) {
    return atof(s.ptr);
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

/* ------------------------------------------------------------------ */
/* Socket / HTTP server                                                */
/* ------------------------------------------------------------------ */

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int64_t mx_http_listen(int64_t port) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return -1;
    
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((uint16_t)port);
    
    if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) return -2;
    if (listen(sock, 10) < 0) return -3;
    
    return (int64_t)sock;
}

int64_t mx_http_accept(int64_t server_sock) {
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    int client = accept((int)server_sock, (struct sockaddr*)&client_addr, &client_len);
    return (int64_t)client;
}

mx_str mx_http_recv(int64_t client_sock) {
    char buf[4096];
    ssize_t n = recv((int)client_sock, buf, sizeof(buf) - 1, 0);
    if (n <= 0) return mx_str_lit("");
    buf[n] = '\0';
    
    mx_str s;
    s.ptr = strdup(buf);
    s.len = n;
    return s;
}

int64_t mx_http_send(int64_t client_sock, mx_str body) {
    const char* header = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: ";
    char len_buf[32];
    snprintf(len_buf, sizeof(len_buf), "%ld\r\n\r\n", (long)body.len);
    
    send((int)client_sock, header, strlen(header), 0);
    send((int)client_sock, len_buf, strlen(len_buf), 0);
    send((int)client_sock, body.ptr, (size_t)body.len, 0);
    
    close((int)client_sock);
    return 0;
}
