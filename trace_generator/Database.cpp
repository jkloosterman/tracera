#include "Database.h"
#include <cassert>
#include <iostream>
#include <fstream>
using namespace std;

Database::Database(SqliteDB &_sqliteDB)
    : sqliteDB(_sqliteDB)
{
    nextMemId = 0;
    benchmarkId = 0;
}

void Database::registerBB(int bbId, vector<BBInstructions::BBInstruction> &instructions)
{
    DBTrace trace;

    Chunk cur;
    for (unsigned i = 0; i < instructions.size(); i++)
    {
	if (instructions[i] == BBInstructions::LOAD || instructions[i] == BBInstructions::STORE)
	{
	    if (cur.size())
	    {
		unsigned id = chunkIdx(cur);
		DBTraceNode ctn;
		ctn.type = DBTraceNode::CHUNK;
		ctn.chunk_id = id;
		trace.push_back(ctn);
		cur.clear();
	    }

	    DBTraceNode mtn;
	    if (instructions[i] == BBInstructions::LOAD)
		mtn.type = DBTraceNode::LOAD;
	    else
		mtn.type = DBTraceNode::STORE;

	    mtn.mem_id = nextMemId;
	    nextMemId++;
	    trace.push_back(mtn);
	}
	else if (instructions[i] == BBInstructions::INTEGER)
	{
	    cur.push_back(INTEGER);
	}
	else if (instructions[i] == BBInstructions::FP)
	{
	    cur.push_back(FLOAT);
	}
	else
	{
	    assert(false && "Unknown instruction type.");
	}
    }

    if (cur.size())
    {
	unsigned id = chunkIdx(cur);
	DBTraceNode ctn;
	ctn.type = DBTraceNode::CHUNK;
	ctn.chunk_id = id;
	trace.push_back(ctn);
	cur.clear();
    }

    bbTraces[bbId] = trace;
}

int Database::memAccessesInBB(int bbId)
{
    int accesses = 0;

    DBTrace &trace = bbTraces[bbId];
    for (unsigned i = 0; i < trace.size(); i++)
    {
	DBTraceNode &tn = trace[i];
	if (tn.type == DBTraceNode::LOAD || tn.type == DBTraceNode::STORE)
	    accesses++;
    }    

    return accesses;
}

void Database::dumpBB(BBId bbId)
{
    cout << "BB " << bbId << ":";

    DBTrace &trace = bbTraces[bbId];
    for (unsigned i = 0; i < trace.size(); i++)
    {
	DBTraceNode &tn = trace[i];
	if (tn.type == DBTraceNode::LOAD)
	    cout << "L";
	else if (tn.type == DBTraceNode::STORE)
	    cout << "S";
	else
	    cout << chunkToString(chunks[tn.chunk_id]);
    }
    cout << endl;
}

unsigned Database::chunkIdx(Chunk &c)
{
    // Return if found in index
    string chunkString = chunkToString(c);
    if (chunkIndex.find(chunkString) != chunkIndex.end())
	return chunkIndex[chunkString];

    // Otherwise insert it
    unsigned idx = chunks.size();
    chunks.push_back(c);
    chunkIndex[chunkString] = idx;

    return idx;
}

string Database::chunkToString(Chunk &c)
{
    string s;

    for (unsigned i = 0; i < c.size(); i++)
    {
	if (c[i] == INTEGER)
	    s += "I";
	else if (c[i] == FLOAT)
	    s += "F";
	else
	    assert(false && "Bad instruction in chunk.");
    }

    return s;
}

unsigned Database::insertTrace(vector<TraceNode> &trace)
{   
    if (traceIndex.find(trace) != traceIndex.end())
	return traceIndex[trace];

    for (unsigned i = 0; i < trace.size(); i++)
	assert(trace[i].type != TraceNode::CHILD_LOOP);

    // Otherwise insert it
    unsigned idx = traces.size();
    traces.push_back(trace);
    traceIndex[trace] = idx;

    return idx;
}

/*
 How to handle iterations:
  -don't want to have state in Database.
  -current loop is a std::list of MemoryTraces.
  -then on commit, we go through and try to deduplicate them.
  -but on insertIteration, we need to re-use memoryTraces if possible.
*/

void Database::insertIteration(unsigned iterationId, LoopTrace &trace)
{
    unsigned traceId = insertTrace(trace.trace);
    assert(trace.trace.size() == trace.accesses.size());

    // Find the MemoryTrace in this loop for the trace.
    for (unsigned i = 0; i < trace.memTraces.size(); i++)
    {
	MemoryTrace &mt = trace.memTraces[i];

	if (mt.traceId == traceId)
	{
	    mt.addIteration(iterationId, trace.accesses);
	    trace.iterationToMemtrace.push_back(i);
	    return;
	}
    }

    // New memTrace
    MemoryTrace mt(traceId, trace.trace.size());
    trace.iterationToMemtrace.push_back(trace.memTraces.size());
    trace.memTraces.push_back(mt);
    trace.memTraces.back().addIteration(iterationId, trace.accesses);
}

void Database::insertLoop(LoopTrace &trace)
{
    unsigned loopId = sqliteDB.getLoopId();
    dynamicIdToLoop[trace.dynamicId] = loopId;

    std::vector<unsigned> memTraceIds;
    for (unsigned i = 0; i < trace.memTraces.size(); i++)
    {
	unsigned memTraceId = trace.memTraces[i].dumpSql(benchmarkId, sqliteDB);
	memTraceIds.push_back(memTraceId);
    }

    unsigned numIterations = trace.curIteration + 1;
    assert(numIterations == trace.iterationToMemtrace.size());

    for (unsigned i = 0; i < numIterations; i++)
    {
	unsigned memTraceId = trace.iterationToMemtrace[i];
	assert(memTraceId < trace.memTraces.size());

	sqliteDB.insertLoop(loopId, trace.staticId, i, trace.memTraces[memTraceId].traceId, memTraceIds[memTraceId]);
    }
}

// We are interested in 2 things: the child dynamic ID and some
// unique ID that will say which other children it's coalesceable with.
void Database::mergeChildLoops(std::vector<TraceNode> &trace)
{
    for (unsigned i = 0; i < trace.size(); i++)
    {
	TraceNode &n = trace[i];
	if (n.type != TraceNode::CHILD_LOOP)
	    continue;

	unsigned childId = n.childDynamicId;
	if (dynamicIdToLoop.find(childId) == dynamicIdToLoop.end())
	{
	    assert(false && "Child dynamic ID must have been previously inserted.");
	    abort();
	}

	n.mergedChildId = dynamicIdToLoop[childId];
	n.type = TraceNode::MERGED_CHILD_LOOP;
    }
}

void Database::dump()
{
    cout << bbTraces.size() << " BBs" << endl;

    cout << chunks.size() << " chunks:" << endl;
    for (unsigned i = 0; i < chunks.size(); i++)
    {
	cout << i << ": " << chunkToString(chunks[i]) << endl;
    }

    cout << "Traces: " << traces.size() << endl;
    cout << "Loops: " << sqliteDB.getLoopId() << endl;

/*
    for (unsigned i = 0; i < iterations.size(); i++)
    {
	cout << "Iteration " << i << "\n=====\n";
	iterations[i].dumpSql(cout);
    }
*/
}

void Database::dumpSql()
{
    for (unsigned i = 0; i < chunks.size(); i++)
    {
	sqliteDB.insertChunk(i, chunkToString(chunks[i]));
    }

    for (auto it = bbTraces.begin(); it != bbTraces.end(); ++it)
    {
	DBTrace &dbTrace = it->second;

	for (unsigned j = 0; j < dbTrace.size(); j++)
	{
	    unsigned type;
	    if (dbTrace[j].type == DBTraceNode::CHUNK)
		type = 0;
	    else if (dbTrace[j].type == DBTraceNode::LOAD)
		type = 1;
	    else
		type = 2;

	    unsigned componentId = sqliteDB.insertBasicBlockComponent( 
		type,
		(dbTrace[j].type == DBTraceNode::CHUNK ? dbTrace[j].chunk_id : 0));
	    sqliteDB.insertBasicBlock(it->first, j, componentId);
	}
    }


    for (unsigned i = 0; i < traces.size(); i++)
    {
	Trace &t = traces[i];

	for (unsigned j = 0; j < t.size(); j++)
	{
	    // type = 0: basic block
	    // type = 1: merged child loop

	    TraceNode &n = t[j];
	    assert(n.type == TraceNode::BASIC_BLOCK || n.type == TraceNode::MERGED_CHILD_LOOP);

	    sqliteDB.insertTrace(
		i, j, 
		(n.type == TraceNode::BASIC_BLOCK ? 0 : 1 ),
		(n.type == TraceNode::BASIC_BLOCK ? n.bbId : 0 ),
		(n.type == TraceNode::MERGED_CHILD_LOOP ? n.mergedChildId : 0 ));
	}
    }
    
}
