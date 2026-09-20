/*
 * Maxx Minimal Runtime (Level 1 bootstrap).
 *
 * A tiny, dependency-free runtime: malloc-backed strings, print function,
 * channels, file IO, and time. This exists only to run bootstrap programs;
 * the production runtime (GC, scheduler, real IO) is a Level 2+ concern.
 */
#ifndef MAXX_RUNTIME_MINIMAL_H
#define MAXX_RUNTIME_MINIMAL_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* Maxx string: a length-buffered, immutable UTF-8 slice. */
typedef struct {
    const char* ptr;
    int64_t len;
} mx_str;

/* Construct an mx_str from a C string literal. */
mx_str mx_str_lit(const char* s);

/* Concatenate two mx_str values (allocates a new buffer). */
mx_str mx_str_concat(mx_str a, mx_str b);

/* Print an mx_str followed by a newline. */
void mx_println(mx_str s);

/* Print an mx_str without newline. */
void mx_print(mx_str s);

/* Numeric -> string conversions. */
mx_str mx_int_to_str(int64_t v);
mx_str mx_double_to_str(double v);
mx_str mx_bool_to_str(bool v);

/* IO: read a line from stdin. */
mx_str mx_read_line(void);

/* IO: read entire file. */
mx_str mx_read_file(mx_str path);

/* IO: write string to file, returns bytes written. */
int64_t mx_write_file(mx_str path, mx_str content);

/* Time: current unix timestamp in seconds (as double). */
double mx_now_sec(void);

/* Time: sleep for given seconds. */
void mx_sleep(double secs);

/* Minimal channel (bounded, synchronous, single-threaded stub). */
typedef struct mx_chan_str mx_chan_str;

mx_chan_str* mx_chan_str_new(void);
void mx_chan_str_send(mx_chan_str* ch, mx_str s);
mx_str mx_chan_str_recv(mx_chan_str* ch);

#endif /* MAXX_RUNTIME_MINIMAL_H */
