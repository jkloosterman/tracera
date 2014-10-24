#ifndef _TRACER_H
#define _TRACER_H

#include "BBInstructions.h"
#include "Cache.h"
#include "MemoryTrace.h"
#include "TraceAccess.h"
#include <unordered_map>
#include <map>
#include <sstream>
#include <list>

class Database;

struct TraceNode {
    enum {
	BASIC_BLOCK,
	CHILD_LOOP,
	MERGED_CHILD_LOOP
    } type;
    
    union {
	BBId bbId;
	unsigned childDynamicId;
	unsigned mergedChildId;
    };

    bool operator==(const TraceNode &other) const {
	if (type != other.type)
	    return false;
	else if (type == BASIC_BLOCK && bbId != other.bbId)
	    return false;
	else if (type == CHILD_LOOP && childDynamicId != other.childDynamicId)
	    return false;
	else if (type == MERGED_CHILD_LOOP && mergedChildId != other.mergedChildId)
	    return false;

	return true;
    }
};

struct LoopTrace
{
    int staticId;
    int dynamicId;
    int curIteration;
    
    std::vector<std::vector<TraceAccess>> accesses;
    std::vector<TraceNode> trace;
    std::vector<MemoryTrace> memTraces;
    std::vector<int> iterationToMemtrace;
};

// this class will maintain the BB stack to ignore BBs within BBs.
class Tracer
{
public:
    Tracer(Database &_database);
    void startLoop(int staticId);
    void endLoop(int staticId);
    void loopHeader(int staticId);
    void basicBlockStart(BBId bbId);
    void basicBlockEnd(BBId bbId);
    void memoryRead(void *base, unsigned size, BBId bbId);
    void memoryWrite(void *base, unsigned size, BBId bbId);
    
private:
    int nextDynamicId;
    void memoryAccess(void *base, unsigned size, BBId bbId, TraceAccessType type);

    int activeIdx;
    Database &database;
    std::vector<LoopTrace> traces;
    std::vector<BBId> bbStack;

    int skidBufferBB;
    std::vector<TraceAccess> memSkidBuffer;
};

#endif
