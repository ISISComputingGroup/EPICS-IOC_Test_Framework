# These PVs will prevent a motor from moving while the CAEN is on
epicsEnvSet(PVONE,$(MYPVPREFIX)SIMPLE:VALUE1:SP)
epicsEnvSet(PVTWO,$(MYPVPREFIX)SIMPLE:VALUE2:SP)
epicsEnvSet(PVONE_DISP,$(MYPVPREFIX)SIMPLE:VALUE1:SP.DISP)
epicsEnvSet(PVTWO_DISP,$(MYPVPREFIX)SIMPLE:VALUE2:SP.DISP)

## Start any sequence programs
seq inhibitor, "PVONE=$(PVONE),PVTWO=$(PVTWO),PVONE_DISP=$(PVONE_DISP),PVTWO_DISP=$(PVTWO_DISP)"
