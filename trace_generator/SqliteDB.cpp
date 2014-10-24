#include <cassert>
#include <vector>
#include <iostream>
#include "SqliteDB.h"
using namespace std;

SqliteDB::SqliteDB()
{
    curComponentId = 0;
    curLoopId = 0;
    curMemTraceId = 0;
    curMemNodeId = 0;
    curMemAddressNodeId = 0;
}

void SqliteDB::open(string filename)
{
    char * sErrMsg = 0;
    SQL_ASSERT(sqlite3_open(filename.c_str(), &_db));

    vector<string> createStmts = {
	"CREATE TABLE chunks (chunkId INTEGER PRIMARY KEY, chunk TEXT);"
	"CREATE TABLE basicBlockComponents (componentId INTEGER PRIMARY KEY, type INTEGER, chunkId INTEGER);",
	"CREATE TABLE basicBlocks (basicBlockId INTEGER, sequence INTEGER, componentId INTEGER);",
	"CREATE TABLE traces (traceId INTEGER, sequence INTEGER, type INTEGER, basicBlockId INTEGER, childLoopId INTEGER);",
	"CREATE TABLE loops (loopId INTEGER, staticId INTEGER, iteration INTEGER, traceID INTEGER, memoryTraceId INTEGER);",
	"CREATE TABLE memoryTraces (memoryTraceId INTEGER, bbSequence INTEGER, sequence INTEGER, memoryTraceNodeId INTEGER);",
	"CREATE TABLE memoryTraceNodes (memoryTraceNodeId INTEGER PRIMARY KEY, type INTEGER, size INTEGER, base INTEGER, coefficient INTEGER, baseIteration INTEGER);",
	"CREATE TABLE memoryTraceNodeAddresses (memoryTraceNodeAddressId INTEGER PRIMARY KEY, memoryTraceNodeId INTEGER, iteration INTEGER, address INTEGER);"
    };

    for (unsigned i = 0; i < createStmts.size(); i++)
    {
	SQL_ASSERT(sqlite3_exec(
	    _db,
	    createStmts[i].c_str(),
	    NULL, NULL, &sErrMsg));
    }

    SQL_ASSERT(sqlite3_exec(_db, "PRAGMA synchronous = OFF", NULL, NULL, &sErrMsg));
    SQL_ASSERT(sqlite3_exec(_db, "BEGIN TRANSACTION", NULL, NULL, &sErrMsg));

    const char *tail;

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO chunks VALUES ("
		   "@chunkId, @chunk );",
		   -1, &chunkStmt, &tail));
    assert(chunkStmt);

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO basicBlockComponents VALUES ("
		   "@componentId, @type, @chunkId );",
		   -1, &componentStmt, &tail));
    assert(componentStmt);

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO basicBlocks VALUES ("
		   "@basicBlockId, @sequence, @componentId );",
		   -1, &bbStmt, &tail));
    assert(bbStmt);

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO traces VALUES ("
		   "@traceId, @sequence, @type, @basicBlockId, @childLoopId);",
		   -1, &traceStmt, &tail));
    assert(traceStmt);

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO loops VALUES ("
		   "@loopId, @staticId, @iteration, @traceId, @memTraceId);",
		   -1, &loopStmt, &tail));
    assert(loopStmt);

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO memoryTraces (memoryTraceId, bbSequence, sequence, memoryTraceNodeId) VALUES ( "
		   "@traceId, @bbSequence, @sequence, @nodeId);",
		   -1, &memoryTraceStmt, &tail));
    assert(memoryTraceStmt);

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO memoryTraceNodes (memoryTraceNodeId, type, size, base, coefficient, baseIteration) VALUES ( "
		   "@nodeId, @type, @size, @base, @coefficient, @baseIteration);",
		   -1, &memoryTraceNodeStmt, &tail));
    assert(memoryTraceNodeStmt);

    SQL_ASSERT(sqlite3_prepare_v2(
		   _db,
		   "INSERT INTO memoryTraceNodeAddresses (memoryTraceNodeAddressId, memoryTraceNodeId, iteration, address) VALUES ("
		   "@addrId, @nodeId, @iteration, @address );",
		   -1, &memoryTraceNodeAddressStmt, &tail));
    assert(memoryTraceNodeAddressStmt);


}

void SqliteDB::close()
{
    char * sErrMsg = 0;
    SQL_ASSERT(sqlite3_exec(_db, "END TRANSACTION", NULL, NULL, &sErrMsg));
    sqlite3_close(_db);
}

unsigned SqliteDB::getMemoryTraceId()
{
    unsigned id = curMemTraceId;
    curMemTraceId++;
    return id;
}

unsigned SqliteDB::insertMemoryTraceNode(
    unsigned memTraceId, unsigned bbSequence, unsigned sequence, unsigned size, unsigned type,
    void *base, unsigned coefficient, unsigned baseIteration)
{
    unsigned id = curMemNodeId;

    sqlite3_bind_int(memoryTraceStmt, 1, memTraceId);
    sqlite3_bind_int(memoryTraceStmt, 2, bbSequence);
    sqlite3_bind_int(memoryTraceStmt, 3, sequence);
    sqlite3_bind_int(memoryTraceStmt, 4, id);
    assert(sqlite3_step(memoryTraceStmt) == SQLITE_DONE);
    sqlite3_reset(memoryTraceStmt);
    
    sqlite3_bind_int(memoryTraceNodeStmt, 1, id);
    sqlite3_bind_int(memoryTraceNodeStmt, 2, type);
    sqlite3_bind_int(memoryTraceNodeStmt, 3, size);
    sqlite3_bind_int64(memoryTraceNodeStmt, 4, (long) base);
    sqlite3_bind_int(memoryTraceNodeStmt, 5, coefficient);
    sqlite3_bind_int(memoryTraceNodeStmt, 6, baseIteration);
    assert(sqlite3_step(memoryTraceNodeStmt) == SQLITE_DONE);
    sqlite3_reset(memoryTraceNodeStmt);

    curMemNodeId++;
    return id;
}

unsigned SqliteDB::insertMemoryAddressNode(
    unsigned memoryTraceNodeId, unsigned iteration, void *address)
{
    unsigned id = curMemAddressNodeId;

    sqlite3_bind_int(memoryTraceNodeAddressStmt, 1, id);
    sqlite3_bind_int(memoryTraceNodeAddressStmt, 2, memoryTraceNodeId);
    sqlite3_bind_int(memoryTraceNodeAddressStmt, 3, iteration);
    sqlite3_bind_int64(memoryTraceNodeAddressStmt, 4, (long) address);
    assert(sqlite3_step(memoryTraceNodeAddressStmt) == SQLITE_DONE);
    sqlite3_reset(memoryTraceNodeAddressStmt);

    curMemAddressNodeId++;
    return id;
}


void SqliteDB::insertChunk(unsigned chunkId, string chunk)
{
    sqlite3_bind_int(chunkStmt, 1, chunkId);
    sqlite3_bind_text(chunkStmt, 2, chunk.c_str(), -1, SQLITE_TRANSIENT);
    assert(sqlite3_step(chunkStmt) == SQLITE_DONE);
    sqlite3_reset(chunkStmt);
}


// type == 0: chunk, type == 1: load, type == 2: store
unsigned SqliteDB::insertBasicBlockComponent(unsigned type, unsigned chunkId)
{
    int id = curComponentId;

    sqlite3_bind_int(componentStmt, 1, id);
    sqlite3_bind_int(componentStmt, 2, type);
    sqlite3_bind_int(componentStmt, 3, chunkId);
    assert(sqlite3_step(componentStmt) == SQLITE_DONE);
    sqlite3_reset(componentStmt);

    curComponentId++;
    return id;
}

void SqliteDB::insertBasicBlock(unsigned bbId, unsigned sequence, unsigned componentId)
{
    sqlite3_bind_int(bbStmt, 1, bbId);
    sqlite3_bind_int(bbStmt, 2, sequence);
    sqlite3_bind_int(bbStmt, 3, componentId);
    assert(sqlite3_step(bbStmt) == SQLITE_DONE);
    sqlite3_reset(bbStmt);
}

void SqliteDB::insertTrace(unsigned traceId, unsigned sequence, unsigned type, unsigned bbId, unsigned childId)
{
    sqlite3_bind_int(traceStmt, 1, traceId);
    sqlite3_bind_int(traceStmt, 2, sequence);
    sqlite3_bind_int(traceStmt, 3, type);
    sqlite3_bind_int(traceStmt, 4, bbId);
    sqlite3_bind_int(traceStmt, 5, childId);
    assert(sqlite3_step(traceStmt) == SQLITE_DONE);
    sqlite3_reset(traceStmt);
}

unsigned SqliteDB::getLoopId()
{
    int id = curLoopId;
    curLoopId++;
    return id;
}

void SqliteDB::insertLoop(unsigned loopId, unsigned staticId, unsigned iteration, unsigned traceId, unsigned memTraceId)
{
    sqlite3_bind_int(loopStmt, 1, loopId);
    sqlite3_bind_int(loopStmt, 2, staticId);
    sqlite3_bind_int(loopStmt, 3, iteration);
    sqlite3_bind_int(loopStmt, 4, traceId);
    sqlite3_bind_int(loopStmt, 5, memTraceId);
    assert(sqlite3_step(loopStmt) == SQLITE_DONE);
    sqlite3_reset(loopStmt);
}

