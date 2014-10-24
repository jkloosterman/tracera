#ifndef _TRACE_ACCESS_H
#define _TRACE_ACCESS_H

enum TraceAccessType {
    READ,
    WRITE
};

struct TraceAccess {
    void *address;
    unsigned size;
    TraceAccessType type;
};

#endif
