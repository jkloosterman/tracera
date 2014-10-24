#include <iostream>
#include <cassert>
#include <signal.h>

#include "Tracer.h"
#include "Database.h"
using namespace std;

#include <signal.h>
void johnAssert(bool result)
{
    if (!result)
    {
        raise(SIGTRAP);
        assert(false);
    }
}


Tracer::Tracer(Database &_database)
    : database(_database)
{
    nextDynamicId = 0;
    activeIdx = 0;
    skidBufferBB = -1;
}

void Tracer::startLoop(int staticId)
{
//    cout << "Start, staticId: " << staticId << endl;

    if (traces.size())
    {
	TraceNode tn;
	tn.type = TraceNode::CHILD_LOOP;
	tn.childDynamicId = nextDynamicId;
	traces.back().trace.push_back(tn);

	vector<TraceAccess> p;
	traces.back().accesses.push_back(p);
    }

    traces.resize(traces.size() + 1);
    traces.back().staticId = staticId;
    traces.back().dynamicId = nextDynamicId;
    traces.back().curIteration = -1;

    // The old loop is active until we reach
    //  the loop header of the new loop.
    activeIdx = 1;
    nextDynamicId++;
}

void Tracer::endLoop(int staticId)
{
//    cout << "End, staticId: " << staticId << endl;

    // Insert the last iteration
    if (traces.back().trace.size())
    {
	database.mergeChildLoops(traces.back().trace);
	database.insertIteration(traces.back().curIteration, traces.back());
    }

    database.insertLoop(traces.back());
    traces.pop_back();
}

void Tracer::loopHeader(int staticId)
{
//    cout << "Header, staticId: " << staticId << endl;

    activeIdx = 0;
    assert(traces.back().staticId == staticId);

    if (traces.back().trace.size())
    {
	assert(traces.back().curIteration >= 0);

	database.mergeChildLoops(traces.back().trace);
	database.insertIteration(traces.back().curIteration, traces.back());

	traces.back().trace.clear();
	traces.back().accesses.clear();
    }

    traces.back().curIteration++;
}

void Tracer::basicBlockStart(BBId bbId)
{
    /*
     * Note that Pin has a different version of basic block
     *  than we usually expect. In particular, an instruction
     *  may be in multiple BBs. In this case, we will have
     *  instrumented the BB more than once. The first call
     *  to BBStart wins.
     */

//    cout << "Start: " << bbId << endl;

    if (!traces.size())
	return;
    if (bbStack.size())
	return;

    // Don't record anything if there is a loop on the stack
    //  but its header hasn't fired yet.
    if (traces.size() == 1 && activeIdx > 0)
	return;

    bbStack.push_back(bbId);
//    cout << "Kept start: " << bbId << endl;
    

    TraceNode tn;
    tn.type = TraceNode::BASIC_BLOCK;
    tn.bbId = bbId;

    LoopTrace &t = traces[traces.size() - 1 - activeIdx];


    /* Temp: verify that we got the correct number of memory accesses
       in the previous BB. */
    if (t.trace.size() && t.trace.back().type == TraceNode::BASIC_BLOCK)
    {
	unsigned bbAccesses = database.memAccessesInBB(t.trace.back().bbId);
	unsigned accesses = t.accesses.back().size();
	assert(bbAccesses == accesses);
/*
	
	if (bbAccesses != accesses)
	{
	    cout << "****************** ERRROR ***********" << endl;
	    database.dumpBB(t.trace.back().bbId);
	    cout << "bbAccesses: " << bbAccesses << ", accesses: " << accesses << endl;
	    abort();
	}
	else
	{
	    cout << "Number of accesses good!" << endl;
	}
*/

    }
    
    t.trace.push_back(tn);    
    vector<TraceAccess> p;
    t.accesses.push_back(p);
    assert(t.trace.size() == t.accesses.size());


    if (skidBufferBB == bbId)
    {
	for (auto it = memSkidBuffer.begin(); it != memSkidBuffer.end(); ++it)
	{
	    memoryAccess(it->address, it->size, bbId, it->type);
	}

	skidBufferBB = -1;
	memSkidBuffer.clear();
    }
}

void Tracer::basicBlockEnd(BBId bbId)
{
//    cout << "End: " << bbId << endl;

    // If this isn't the current basic block,
    //  ignore it.
    if (bbStack.size() && bbId == bbStack.back())
    {
//	cout << "Kept end: " << bbId << endl;
	bbStack.pop_back();
    }
}

void Tracer::memoryRead(void *base, unsigned size, BBId bbId)
{
    memoryAccess(base, size, bbId, TraceAccessType::READ);
}

void Tracer::memoryWrite(void *base, unsigned size, BBId bbId)
{
    memoryAccess(base, size, bbId, TraceAccessType::WRITE);
}

void Tracer::memoryAccess(void *base, unsigned size, BBId bbId, TraceAccessType type)
{
//    cout << "Pre-access: " << bbId << ", ";
/*
    if (type == TraceAccessType::READ)
	cout << "load";
    else
	cout << "store";
    cout << endl;
*/

    if (!bbStack.size())
    {
	if (skidBufferBB != bbId)
	{
	    skidBufferBB = bbId;
	    memSkidBuffer.clear();
	}
	    
	TraceAccess a;
 	a.address = base;
	a.size = size;
	a.type = type;

	memSkidBuffer.push_back(a);
	return;
    }

    if (!traces.size())
	return;

    // covers the case where there's no loop to attribute the
    //  load to.
    if (traces.size() == 1 && activeIdx == 1)
	return;

//    cout << "Access: " << bbId << endl;

    assert(bbId == bbStack.back());

    LoopTrace &t = traces[traces.size() - 1 - activeIdx];
    assert(t.accesses.size() == t.trace.size());
    assert(!t.accesses.empty());

    TraceAccess a;
    a.address = base;
    a.size = size;
    a.type = type;

    t.accesses.back().push_back(a);
}
