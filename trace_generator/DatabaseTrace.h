#ifndef _DB_TRACE_H
#define _DB_TRACE_H

enum InstructionType
{
    INTEGER,
    FLOAT
};

struct DBTraceNode
{
    enum {
	LOAD,
	STORE,
	CHUNK
    } type;
    
    union {
	unsigned mem_id;
	unsigned chunk_id;
    };
};

typedef std::vector<DBTraceNode> DBTrace;

#endif
