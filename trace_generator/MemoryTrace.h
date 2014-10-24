#ifndef _MEMORY_TRACE_H
#define _MEMORY_TRACE_H

#include "SqliteDB.h"
#include "TraceAccess.h"
#include <vector>
#include <iostream>
#include <unordered_set>

struct TraceNode;

class MemoryTraceNode
{
public:
    // This automatically transforms itself between the
    //  memory access patterns.
    MemoryTraceNode() 
	: type(UNINITIALIZED) {}
    void addAccess(unsigned iterationId, TraceAccess &access);
    void dumpSql(unsigned memTraceId, unsigned bbSequence, unsigned sequence, SqliteDB &db);

    size_t hash() const;
    bool operator==(const MemoryTraceNode &other) const;
    unsigned numAddresses() const;

    unsigned size;
private:
    enum AccessType {
	CONSTANT,
	LINEAR,
	RANDOM,
	UNINITIALIZED
    };

    AccessType type;
    TraceAccessType rwType;

    union {
	void *constantAddress;
	struct {
	    void *linearBase;
	    int linearCoefficient;
	    unsigned linearBaseIteration;
	};
    };
    std::vector<void *> randomAddresses;
    std::vector<unsigned> iterations;
};


class MemoryTrace
{
public:
    MemoryTrace(unsigned _traceId, unsigned _traceSize);
    void addIteration(unsigned iterationId, std::vector<std::vector<TraceAccess> > &accesses);

    unsigned dumpSql(unsigned benchmarkId, SqliteDB &db);
    unsigned traceId;

    size_t hash() const;
    bool operator==(const MemoryTrace &other) const;
    unsigned size() const;
    unsigned numAddresses() const;
    bool hasIteration (unsigned iterationId);
private:
//    unsigned lastHash;
//    bool lastHashValid;

    void fixAccesses(std::vector<MemoryTraceNode> &existingMemTrace, std::vector<TraceAccess> &accesses);
    std::vector<std::vector<MemoryTraceNode> > mtNodes;
    std::unordered_set<unsigned> iterations;
};

#endif
