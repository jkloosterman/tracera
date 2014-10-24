CREATE INDEX bb_idx ON basicBlocks (basicBlockId, sequence);
CREATE INDEX tr_idx ON traces (traceId, sequence);
CREATE INDEX lp_idx ON loops (loopId, iteration);
CREATE INDEX mt_idx ON memoryTraces (memoryTraceId, bbSequence, sequence);
CREATE INDEX mn_idx ON memoryTraceNodeAddresses (memoryTraceNodeId, iteration);