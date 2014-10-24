#ifndef _INSTRUCTIONS_H
#define _INSTRUCTIONS_H

#include <unordered_map>
#include <vector>
#include "pin.H"

class Database;
typedef int BBId;

class BBInstructions
{
public:
    BBInstructions(Database &_database);
    void startBB(BBId bbId);
    void endBB();
    void addInstruction(INS ins);
    void addLoad();
    void addStore();

    enum BBInstruction {
	INTEGER,
	FP,
	UNCOND_BRANCH,
	LOAD,
	STORE
    };

private:
    Database &database;
    BBInstruction classifyInstruction(INS ins);

    unsigned curBB;
    std::vector<BBInstruction> curInstructions;

};

#endif
