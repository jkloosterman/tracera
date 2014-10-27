/**
 * @author John Kloosterman
 * @date Oct. 7, 2014
 */

#include <cassert>

#include "MemoryTrace.h"
#include "Tracer.h"
#include "Hashes.h"
using namespace std;

MemoryTrace::MemoryTrace(unsigned _traceId, unsigned _traceSize)
    : traceId(_traceId)
{
    assert(_traceSize > 0);
    mtNodes.resize(_traceSize);
//    lastHashValid = false;
}

void MemoryTrace::fixAccesses(vector<MemoryTraceNode> &existingMemTrace, vector<TraceAccess> &accesses)
{
    vector<TraceAccess> newAccesses;

    // If there are the wrong number of accesses for this BB,
    //  try to fix things up.
    if (existingMemTrace.size() == accesses.size())
	return;

    // But only if we have more accesses than were in the
    //  trace.
    assert(existingMemTrace.size() < accesses.size());

    for (unsigned i = 0; i < existingMemTrace.size(); i++)
    {
	for (auto it = accesses.begin(); it != accesses.end(); ++it)
	{
	    if (existingMemTrace[i].size == it->size)
	    {
		newAccesses.push_back(*it);

		// Deleting from a vector. But this is an uncommon case.
		accesses.erase(it);

		break;
	    }
	}
    }

    accesses = newAccesses;
}

void MemoryTrace::addIteration(unsigned iterationId, vector<vector<TraceAccess> > &accesses)
{
//    lastHashValid = false;

    assert(accesses.size() == mtNodes.size());

    unsigned bbIndex = 0;
    for (auto it = accesses.begin(); it != accesses.end(); ++it)
    {
	if (!mtNodes[bbIndex].size())
	    mtNodes[bbIndex].resize(it->size());

	fixAccesses(mtNodes[bbIndex], *it);
	assert(mtNodes[bbIndex].size() == it->size());

	unsigned accessIdx = 0;
	for (auto ait = it->begin(); ait != it->end(); ++ait)
	{
	    mtNodes[bbIndex][accessIdx].addAccess(iterationId, *ait);
	    accessIdx++;
	}

	bbIndex++;
    }

    iterations.insert(iterationId);
}

bool MemoryTrace::hasIteration(unsigned iterationId)
{
    return iterations.find(iterationId) != iterations.end();
}

unsigned MemoryTrace::dumpSql(unsigned benchmarkId, SqliteDB &db)
{
    unsigned memTraceId = db.getMemoryTraceId();

    for (unsigned i = 0; i < mtNodes.size(); i++)
	for (unsigned j = 0; j < mtNodes[i].size(); j++)
	    mtNodes[i][j].dumpSql(memTraceId, i, j, db);

    return memTraceId;
}

unsigned MemoryTrace::size() const
{
    unsigned s = 0;
    for (unsigned i = 0; i < mtNodes.size(); i++)
    {
	s += mtNodes[i].size();
    }

    return s;
}

unsigned MemoryTrace::numAddresses() const
{
    unsigned s = 0;
    for (unsigned i = 0; i < mtNodes.size(); i++)
    {
	for (unsigned j = 0; j < mtNodes[i].size(); j++)
	{
	    s += mtNodes[i][j].numAddresses();
	}
    }

    return s;
}


size_t MemoryTrace::hash() const
{
//    if (lastHashValid)
//	return lastHash;

    size_t hash = traceId;
    for (unsigned i = 0; i < mtNodes.size(); i++)
    {
	for (unsigned j = 0; j < mtNodes[i].size(); j++)
	{
	    hash ^= mtNodes[i][j].hash();
	}
    }
//    lastHash = hash;
    return hash;
}

bool MemoryTrace::operator==(const MemoryTrace &other) const
{
    return 
	mtNodes == other.mtNodes
	&& traceId == other.traceId;
}

void MemoryTraceNode::dumpSql(unsigned memTraceId, unsigned bbSequence, unsigned sequence, SqliteDB &db)
{
    void *base = NULL;
    unsigned offset = 0;
    unsigned baseIteration = 0;
    if (type == CONSTANT)
	base = constantAddress;
    else if (type == LINEAR)
    {
	base = linearBase;
	offset = linearCoefficient;
	baseIteration = linearBaseIteration;
    }

    unsigned memoryTraceNodeId = db.insertMemoryTraceNode(memTraceId, bbSequence, sequence, size, type, base, offset, baseIteration);

    if (type == RANDOM)
    {
	for (unsigned i = 0; i < randomAddresses.size(); i++)
	    db.insertMemoryAddressNode(memoryTraceNodeId, iterations[i], randomAddresses[i]);
    }
}

void MemoryTraceNode::addAccess(unsigned iterationId, TraceAccess &access)
{
    if (type == UNINITIALIZED)
    {
	type = CONSTANT;
	constantAddress = access.address;
	size = access.size;
	rwType = access.type;
    }
    else if (type == CONSTANT)
    {
	assert(access.size == access.size);
	assert(rwType == access.type);

	if (access.address == constantAddress)
	{
	    // do nothing.
	}
	else if (iterations.size() == 1)
	{
	    type = LINEAR;
	    // The previous iteration might not have been iteration 0, so rebase so
	    //  that base + (previous_iteration * coefficient) == constantAddress
	    //  and  base + (current_iteration * coefficient) == access

	    linearBase = constantAddress;
	    linearCoefficient = 
		(int)((unsigned long) access.address - (unsigned long) linearBase) /
		(iterationId - iterations[0]);
	    linearBaseIteration = iterations[0];
	}
	else
	{
	    type = RANDOM;
	    for (auto it = iterations.begin(); it != iterations.end(); ++it)
		randomAddresses.push_back(constantAddress);
	    assert(randomAddresses.size() == iterations.size());
	    randomAddresses.push_back(access.address);
	}
    }
    else if (type == LINEAR)
    {
	assert(access.size == access.size);
	assert(rwType == access.type);

	void *prediction = 
	    (void *)((unsigned long) linearBase 
		     + ((iterationId - linearBaseIteration) * linearCoefficient));
	if (prediction == access.address)
	{
	    // do nothing
	}
	else
	{
	    type = RANDOM;
	    for (auto it = iterations.begin(); it != iterations.end(); ++it)
	    {
		void *ptr = 
		    (void *)((unsigned long) linearBase
			     + ((*it - linearBaseIteration) * linearCoefficient));
		randomAddresses.push_back(ptr);
	    }
	    assert(randomAddresses.size() == iterations.size());
	    randomAddresses.push_back(access.address);
	}
    }
    else if (type == RANDOM)
    {
	assert(access.size == access.size);
	assert(rwType == access.type);
	assert(randomAddresses.size() == iterations.size());

	randomAddresses.push_back(access.address);
    }

    iterations.push_back(iterationId);
}

bool MemoryTraceNode::operator==(const MemoryTraceNode &other) const
{
    if (type != other.type)
	return false;
    if (iterations != other.iterations)
	return false;

    if (type == CONSTANT)
	return constantAddress == other.constantAddress;
    else if (type == LINEAR)
	return linearBase == other.linearBase && linearCoefficient == other.linearCoefficient;
    else if (type == RANDOM)
	return randomAddresses == other.randomAddresses;
    else
	assert(false);
}

size_t MemoryTraceNode::hash() const
{
    std::hash<vector<unsigned>> it_h;
    size_t iterations_hash = it_h(iterations);

    if (type == UNINITIALIZED)
	return 0;
    else if (type == CONSTANT)
	return iterations_hash ^ (size_t) constantAddress;
    else if (type == LINEAR)
	return iterations_hash ^ (size_t) linearBase ^ linearCoefficient;
    else if (type == RANDOM)
    {
	std::hash<vector<void *> > ra_h;
	size_t address_hash = ra_h(randomAddresses);
	return iterations_hash ^ address_hash;
    }
    else
    {
	assert(false);
    }
}

unsigned MemoryTraceNode::numAddresses() const
{
    if (type == UNINITIALIZED)
	return 0;
    else if (type == CONSTANT)
	return 1;
    else if (type == LINEAR)
	return 2;
    else if (type == RANDOM)
	return randomAddresses.size();
    else
	assert(false);
}
