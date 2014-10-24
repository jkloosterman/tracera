/**
 * Records basic blocks executed in loops.
 */

#include <stdio.h>
#include <assert.h>
#include <stack>
#include <fstream>
#include <sys/stat.h>
#include <iostream>
#include "pin.H"
#include "Database.h"
#include "BBInstructions.h"
using namespace std;

#define PTR_INT unsigned long
#define WORD_SIZE 4
#define ROUND_TO_WORD(x) ((x) & (~(WORD_SIZE-1)))

KNOB<string> KnobDatabaseFile(KNOB_MODE_WRITEONCE, "pintool", "df", "out.sqlite", "sqlite output file");

SqliteDB db;
Database database(db);
BBInstructions bbInstructions(database);
Tracer tracer(database);
static unsigned nextBasicBlockId = 0;

VOID RecordMemRead(VOID *ip, VOID * addr, UINT32 size, UINT32 bbId)
{
//    cout << "Read: bbId " << bbId << endl;
    tracer.memoryRead(addr, size, bbId);
}

VOID RecordMemWrite(VOID *ip, VOID * addr, UINT32 size, UINT32 bbId)
{
//    cout << "Write: bbId " << bbId << endl;
    tracer.memoryWrite(addr, size, bbId);
}

VOID RecordInstruction(VOID *ip)
{

}

VOID startLoopCall(int staticLoopId)
{
    tracer.startLoop(staticLoopId);
}

VOID endLoopCall(int staticLoopId)
{
    tracer.endLoop(staticLoopId);
}

VOID loopHeaderCall(int staticLoopId)
{
    tracer.loopHeader(staticLoopId);
}

VOID basicBlockStartCall(int basicBlockId)
{
    tracer.basicBlockStart(basicBlockId);
}

VOID basicBlockEndCall(int basicBlockId)
{
    tracer.basicBlockEnd(basicBlockId);
}

VOID TraceHooks(TRACE trace, VOID *v)
{
    // Visit every basic block  in the trace
    for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl))
    {
	bbInstructions.startBB(nextBasicBlockId);

/*
	if (nextBasicBlockId == 2766 || nextBasicBlockId == 2768)
	{
	    cout << nextBasicBlockId << endl;
	    for (INS ins = BBL_InsHead(bbl); INS_Valid(ins); ins = INS_Next(ins))
	    {
		cout << OPCODE_StringShort(INS_Opcode(ins)) << endl;
	    }
	}
*/

	// Count instruction types in the BB
	for (INS ins = BBL_InsHead(bbl); INS_Valid(ins); ins = INS_Next(ins))
	{
	    // Don't double-instrument instructions.
	    assert(INS_IsOriginal(ins));

	    UINT32 memOperands = INS_MemoryOperandCount(ins);
	    // Iterate over each memory operand of the instruction.
	    if (!INS_IsStackRead(ins))
	    {
		for (UINT32 memOp = 0; memOp < memOperands; memOp++)
		{
		    if (INS_MemoryOperandIsRead(ins, memOp))
		    {
			INS_InsertCall(
			    ins, IPOINT_BEFORE,
			    (AFUNPTR)RecordMemRead,
			    IARG_INST_PTR,
			    IARG_MEMORYOP_EA, memOp,
			    IARG_MEMORYREAD_SIZE,
			    IARG_UINT32, nextBasicBlockId,
			    IARG_END);
			
			bbInstructions.addLoad();
		    }
		}
	    }

	    bbInstructions.addInstruction(ins);

	    if (!INS_IsStackWrite(ins))
	    {
		for (UINT32 memOp = 0; memOp < memOperands; memOp++)
		{
		    if (INS_MemoryOperandIsWritten(ins, memOp))
		    {
			INS_InsertCall(
			    ins, IPOINT_BEFORE,
			    (AFUNPTR)RecordMemWrite,
			    IARG_INST_PTR,
			    IARG_MEMORYOP_EA, memOp,
			    IARG_MEMORYWRITE_SIZE,
			    IARG_UINT32, nextBasicBlockId,
			    IARG_END);

			bbInstructions.addStore();
		    }
		}
	    }
	}
	bbInstructions.endBB();

	// Insert calls for tracing execution of this BB
        INS_InsertCall(BBL_InsHead(bbl), IPOINT_BEFORE, (AFUNPTR)basicBlockStartCall, IARG_UINT32, nextBasicBlockId, IARG_END);
	INS_InsertCall(BBL_InsTail(bbl), IPOINT_BEFORE, (AFUNPTR)basicBlockEndCall, IARG_UINT32, nextBasicBlockId, IARG_END);

	nextBasicBlockId++;
    }
}

VOID Image(IMG img, VOID *v)
{
    RTN startLoop = RTN_FindByName(img, "_startLoop");
    if (RTN_Valid(startLoop))
    {
        RTN_Open(startLoop);
        RTN_InsertCall(startLoop, IPOINT_BEFORE, (AFUNPTR)startLoopCall,
                       IARG_FUNCARG_ENTRYPOINT_VALUE, 0,
                       IARG_END);
        RTN_Close(startLoop);
    }

    RTN endLoop = RTN_FindByName(img, "_endLoop");
    if (RTN_Valid(endLoop))
    {
        RTN_Open(endLoop);
	RTN_InsertCall(endLoop, IPOINT_BEFORE, (AFUNPTR)endLoopCall,
                       IARG_FUNCARG_ENTRYPOINT_VALUE, 0,
                       IARG_END);
        RTN_Close(endLoop);
    }

    RTN loopHeader = RTN_FindByName(img, "_loopHeader");
    if (RTN_Valid(loopHeader))
    {
        RTN_Open(loopHeader);
	RTN_InsertCall(loopHeader, IPOINT_BEFORE, (AFUNPTR)loopHeaderCall,
                       IARG_FUNCARG_ENTRYPOINT_VALUE, 0,
                       IARG_END);
        RTN_Close(loopHeader);
    }

    /* Start/end I/O hooks.
    RTN startIO = RTN_FindByName(img, "_startIO");
    if (RTN_Valid(startIO))
    {
        RTN_Open(startIO);
	RTN_InsertCall(startIO, IPOINT_BEFORE, (AFUNPTR)startIOCall,
                       IARG_END);
        RTN_Close(startIO);
    }

    RTN endIO = RTN_FindByName(img, "_endIO");
    if (RTN_Valid(endIO))
    {
        RTN_Open(endIO);
	RTN_InsertCall(endIO, IPOINT_BEFORE, (AFUNPTR)endIOCall,
                       IARG_END);
        RTN_Close(endIO);
    }
    */
}

VOID Fini(INT32 code, VOID *v)
{
    database.dump();
    database.dumpSql();
    db.close();
}

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */
   
INT32 Usage()
{
    PIN_ERROR( "This Pintool creates a trace of the instructions in all the loops. \n" 
	       + KNOB_BASE::StringKnobSummary() + "\n");
    return -1;
}

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int main(int argc, char *argv[])
{
    PIN_InitSymbols();
    if (PIN_Init(argc, argv)) return Usage();

    db.open(KnobDatabaseFile);

    IMG_AddInstrumentFunction(Image, 0);
    TRACE_AddInstrumentFunction(TraceHooks, 0);
    PIN_AddFiniFunction(Fini, 0);

    // Never returns
    PIN_StartProgram();
    
    return 0;
}
