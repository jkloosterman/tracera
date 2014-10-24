#ifndef _DATABASE_H
#define _DATABASE_H

#include <unordered_map>
#include <map>
#include <vector>
#include <sstream>
#include <list>
#include <fstream>

#include "DatabaseTrace.h"
#include "BBInstructions.h"
#include "Tracer.h"
#include "Hashes.h"
#include "Cache.h"
#include "MemoryTrace.h"
#include "SqliteDB.h"
#include "TraceAccess.h"

class Database
{
public:
    Database(SqliteDB &_sqliteDB);

    void registerBB(int bbId, std::vector<BBInstructions::BBInstruction> &instructions);

    void insertLoop(LoopTrace &trace);
    void insertIteration(unsigned iterationId, LoopTrace &trace);
    void attemptLoopMerge(unsigned loopId);
    void mergeChildLoops(std::vector<TraceNode> &trace);

    void dump();
    void dumpBB(BBId bbId);
    void dumpSql();

    int memAccessesInBB(int bbId);
private:
    int benchmarkId;

    // basic blocks
    std::unordered_map<BBId,DBTrace> bbTraces;

    // chunks
    typedef std::vector<InstructionType> Chunk;
    std::vector<Chunk> chunks;
    std::unordered_map<std::string,int> chunkIndex;
    std::string chunkToString(Chunk &c);

    // rename to insertChunk
    unsigned chunkIdx(Chunk &c);

    // static memory accesses (which are only ID'd, not x-referenced to an object)
    //  these are referred to in DBTraces.
    int nextMemId;

    // traces (lists of BBs and children)
    // traces can be equivalent even if children aren't the same.
    //  dynamicId increments all the time, and staticId isn't safe
    //  because the same staticId can iterate a different number of times.
    // we need the concept of a loop shape/hash or something.
    typedef std::vector<TraceNode> Trace;
    std::vector<Trace> traces;
    std::unordered_map<Trace, unsigned> traceIndex;
    unsigned insertTrace(Trace &trace);

    std::unordered_map<unsigned, unsigned> dynamicIdToLoop;

    SqliteDB &sqliteDB;
    std::stringstream ss;
};

#endif
