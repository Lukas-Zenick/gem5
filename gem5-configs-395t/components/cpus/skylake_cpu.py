"""
CPU modeled loosely on an Intel Skylake.
Sources:
- https://github.com/darchr/gem5-skylake-config
- https://www.csl.cornell.edu/courses/ece4750/handouts/ece4750-section-skylake.pdf

Constructor accepts argument to change the branch predictor (default: TAGE)
"""
from typing import Type
from m5.objects import *
import components.cpus.simargs_o3_cpu as simargs

"""
Set up the functional units within the CPU
"""
class port0(FUDesc):
    opList = [ OpDesc(opClass='IntAlu', opLat=1),
               OpDesc(opClass='IntDiv', opLat=1, pipelined=True),
               OpDesc(opClass='FloatDiv', opLat=12, pipelined=True),
               OpDesc(opClass='FloatSqrt', opLat=24, pipelined=True),
               OpDesc(opClass='FloatAdd', opLat=4, pipelined=True),
               OpDesc(opClass='FloatCmp', opLat=4, pipelined=True),
               OpDesc(opClass='FloatCvt', opLat=4, pipelined=True),
               OpDesc(opClass='FloatMult', opLat=4, pipelined=True),
               OpDesc(opClass='FloatMultAcc', opLat=5, pipelined=True),
               OpDesc(opClass='SimdAdd', opLat=1),
               OpDesc(opClass='SimdAddAcc', opLat=1),
               OpDesc(opClass='SimdAlu', opLat=1),
               OpDesc(opClass='SimdCmp', opLat=1),
               OpDesc(opClass='SimdShift', opLat=1),
               OpDesc(opClass='SimdShiftAcc', opLat=1),
               OpDesc(opClass='SimdReduceAdd', opLat=1),
               OpDesc(opClass='SimdReduceAlu', opLat=1),
               OpDesc(opClass='SimdReduceCmp', opLat=1),
               OpDesc(opClass='SimdCvt', opLat=3, pipelined=True),
               OpDesc(opClass='SimdMisc'),
               OpDesc(opClass='SimdMult', opLat=4, pipelined=True),
               OpDesc(opClass='SimdMultAcc', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatAdd', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatAlu', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatCmp', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatReduceAdd', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatReduceCmp', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatCvt', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatMult', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatMultAcc', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatDiv', opLat=12, pipelined=True),
               OpDesc(opClass='SimdFloatSqrt', opLat=20, pipelined=True)
               ]
    count = 1

class port1(FUDesc):
    opList = [ OpDesc(opClass='IntAlu', opLat=1),
               OpDesc(opClass='IntMult', opLat=3, pipelined=True),
               OpDesc(opClass='FloatAdd', opLat=4, pipelined=True),
               OpDesc(opClass='FloatCmp', opLat=4, pipelined=True),
               OpDesc(opClass='FloatCvt', opLat=4, pipelined=True),
               OpDesc(opClass='FloatMult', opLat=4, pipelined=True),
               OpDesc(opClass='FloatMultAcc', opLat=5, pipelined=True),
               OpDesc(opClass='SimdAdd', opLat=1),
               OpDesc(opClass='SimdAddAcc', opLat=1),
               OpDesc(opClass='SimdAlu', opLat=1),
               OpDesc(opClass='SimdCmp', opLat=1),
               OpDesc(opClass='SimdShift', opLat=1),
               OpDesc(opClass='SimdShiftAcc', opLat=1),
               OpDesc(opClass='SimdReduceAdd', opLat=1),
               OpDesc(opClass='SimdReduceAlu', opLat=1),
               OpDesc(opClass='SimdReduceCmp', opLat=1),
               OpDesc(opClass='SimdCvt', opLat=3, pipelined=True),
               OpDesc(opClass='SimdMisc'),
               OpDesc(opClass='SimdMult', opLat=4, pipelined=True),
               OpDesc(opClass='SimdMultAcc', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatAdd', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatAlu', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatCmp', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatReduceAdd', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatReduceCmp', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatCvt', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatMult', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatMultAcc', opLat=4, pipelined=True)
               ]
    count = 1

class port2(FUDesc):
    opList = [ OpDesc(opClass='MemRead', opLat=1, pipelined=True),
               OpDesc(opClass='FloatMemRead', opLat=1, pipelined=True)
               ]
    count = 1

class port3(FUDesc):
    opList = [ OpDesc(opClass='MemRead', opLat=1, pipelined=True),
               OpDesc(opClass='FloatMemRead', opLat=1, pipelined=True)
               ]
    count = 1

class port4(FUDesc):
    opList = [ OpDesc(opClass='MemWrite', opLat=1, pipelined=True),
               OpDesc(opClass='FloatMemWrite', opLat=1, pipelined=True)
               ]
    count = 1

class port5(FUDesc):
    opList = [ OpDesc(opClass='IntAlu', opLat=1),
               OpDesc(opClass='SimdAdd', opLat=1),
               OpDesc(opClass='SimdAddAcc', opLat=1),
               OpDesc(opClass='SimdAlu', opLat=1),
               OpDesc(opClass='SimdCmp', opLat=1),
               OpDesc(opClass='SimdShift', opLat=1),
               OpDesc(opClass='SimdMisc'),
               OpDesc(opClass='SimdShiftAcc', opLat=1),
               OpDesc(opClass='SimdReduceAdd', opLat=1),
               OpDesc(opClass='SimdReduceAlu', opLat=1),
               OpDesc(opClass='SimdReduceCmp', opLat=1),
               OpDesc(opClass='SimdFloatAdd', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatAlu', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatCmp', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatReduceAdd', opLat=4, pipelined=True),
               OpDesc(opClass='SimdFloatReduceCmp', opLat=4, pipelined=True)
               ]
    count = 1

class port6(FUDesc):
     opList = [ OpDesc(opClass='IntAlu', opLat=1),
                OpDesc(opClass='SimdAdd', opLat=1),
                OpDesc(opClass='SimdAddAcc', opLat=1),
                OpDesc(opClass='SimdAlu', opLat=1),
                OpDesc(opClass='SimdCmp', opLat=1),
                OpDesc(opClass='SimdShift', opLat=1),
                OpDesc(opClass='SimdShiftAcc', opLat=1)
                ]
     count = 1

class port7(FUDesc):
     opList = [ OpDesc(opClass='MemWrite', opLat=1, pipelined=True),
                OpDesc(opClass='FloatMemWrite', opLat=1, pipelined=True)
                ]
     count = 1

class SkylakeExecUnits(FUPool):
    FUList = [ port0(), port1(), port2(), port3(), port4(), port5(), port6(), port7() ]

"""
Configure the TLBs
"""
class SkylakeMMU(X86MMU):
    itb = X86TLB(entry_type="instruction", size=64)
    dtb = X86TLB(entry_type="data", size=64)

"""
Configure the branch predictor(s)
"""

class IndirectPred(SimpleIndirectPredictor):
    indirectSets = 128
    indirectWays = 4
    indirectTagSize = 16
    indirectPathLength = 7
    indirectGHRBits = 16

class LTAGE_BP(LTAGE_TAGE):
    nHistoryTables = 12
    minHist = 4
    maxHist = 34
    tagTableTagWidths = [ 0, 7, 7, 8, 8, 9, 10, 11, 12, 12, 13, 14, 15 ]
    logTagTableSizes = [ 14, 10, 10, 11, 11, 11, 11, 10, 10, 10, 10, 9, 9 ]
    logUResetPeriod = 19

class SkylakeTAGE(LTAGE):
    btb = SimpleBTB(numEntries=512, tagBits=19)
    ras = ReturnAddrStack(numEntries=32)
    indirectBranchPred = IndirectPred()
    tage = LTAGE_BP()
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

# two other branch predictor choices for now, neither configured beyond defaults
class SkylakePerceptron(MultiperspectivePerceptron64KB):
    btb = SimpleBTB(numEntries=512, tagBits=19)
    ras = ReturnAddrStack(numEntries=32)
    indirectBranchPred = IndirectPred()
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

class SkylakeTournament(TournamentBP):
    btb = SimpleBTB(numEntries=512, tagBits=19)
    ras = ReturnAddrStack(numEntries=32)
    indirectBranchPred = IndirectPred()
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

"""
Create an out-of-order CPU with the subunits defined above
"""
# For all CPU options, see src/cpu/o3/BaseO3CPU.py class BaseO3CPU
# (O3CPU will be defined to be X86O3CPU for X86 simulations)
class SkylakeCPU(O3CPU):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Get command-line args related to O3 CPU
        cpu_params = simargs.get_cpu_params()

        # Pipeline delays
        # Scale default 5-stage pipeline by depth
        # Here, we're modeling a 15-stage pipeline
        depth = 3
        self.fetchToDecodeDelay = depth
        self.decodeToRenameDelay = 1
        self.renameToIEWDelay = 3*depth
        self.iewToCommitDelay = 2* depth

        # Pipeline widths
        width = 4
        self.fetchWidth = width
        self.decodeWidth = width
        self.renameWidth = 2*width
        self.dispatchWidth = 2*width
        self.issueWidth = 2*width
        self.wbWidth = 2*width
        self.commitWidth = 2*width
        self.squashWidth = 2*width

        # Functional units
        self.fuPool = SkylakeExecUnits()

        self.forwardComSize = 19
        self.backComSize = 19

        self.fetchBufferSize = 16
        self.fetchQueueSize = 50
        # HINT: These override the inherited class variables, which is
        # fine if you don't plan to change a parameter value often
        #
        # We don't provide any command-line arguments for configuring
        # the CPU, so you'll have to hardcode your values here.
        # 
        # FIXME TODO: Set these appropriately.
        self.numROBEntries = FIXME
        self.numIQEntries = 97
        self.LQEntries = FIXME
        self.SQEntries = FIXME
        self.numPhysIntRegs = 180
        self.numPhysFloatRegs = 168

        # TLBs
        self.mmu = SkylakeMMU()
        
        # Branch predictor: from O3 command line args
        bpred_cls_name = "Skylake" + cpu_params["bpred_type"]
        BranchPredictorCls = getattr(sys.modules[__name__], bpred_cls_name)
        self.branchPred = BranchPredictorCls()
        
        print(f"Creating SkylakeCPU object: bpred={type(self.branchPred)}")
