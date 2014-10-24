#ifndef _SQLITE_DB_H
#define _SQLITE_DB_H

#include <string>
#include <sqlite3.h>
#define SQL_ASSERT(x) assert((x) == SQLITE_OK || (puts(sErrMsg), 0))

class SqliteDB
{
public:
    SqliteDB();
    void open(std::string filename);
    void close();

    unsigned getMemoryTraceId();
    unsigned getLoopId();
    unsigned insertMemoryTraceNode(
	unsigned memTraceId, unsigned bbSequence, unsigned sequence, unsigned size, unsigned type,
	void *base, unsigned coefficient, unsigned baseIteration);
    unsigned insertMemoryAddressNode(unsigned memoryTraceNodeId, unsigned iteration, void *address);
    void insertChunk(unsigned chunkId, std::string chunk);
    unsigned insertBasicBlockComponent(unsigned type, unsigned chunkId);
    void insertBasicBlock(unsigned bbId, unsigned sequence, unsigned componentId);
    void insertTrace(unsigned traceId, unsigned sequence, unsigned type, unsigned bbId, unsigned childId);
    void insertLoop(unsigned loopId, unsigned staticId, unsigned iteration, unsigned traceId, unsigned memTraceId);

private:
    sqlite3 *_db;
    sqlite3_stmt *chunkStmt;
    sqlite3_stmt *componentStmt;
    sqlite3_stmt *bbStmt;
    sqlite3_stmt *traceStmt;
    sqlite3_stmt *loopStmt;
    sqlite3_stmt *memoryTraceStmt;
    sqlite3_stmt *memoryTraceNodeStmt;
    sqlite3_stmt *memoryTraceNodeAddressStmt;

    unsigned curComponentId;
    unsigned curLoopId;
    unsigned curMemTraceId;
    unsigned curMemNodeId;
    unsigned curMemAddressNodeId;
};

#endif
