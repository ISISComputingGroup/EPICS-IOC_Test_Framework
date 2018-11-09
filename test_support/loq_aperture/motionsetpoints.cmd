epicsEnvSet "LOOKUPFILE1" "$(ICPCONFIGROOT)/motionSetPoints/aperture.txt"

motionSetPointsConfigure("LOOKUPFILE1","LOOKUPFILE1")

# The tolerance must be large to make sure that LOCN always points to the closest setpoint
$(IFIOC_GALIL_01) dbLoadRecords("$(MOTIONSETPOINTS)/db/motionSetPoints.db","P=$(MYPVPREFIX)LKUP:APERTURE:,NAME1=APERTURE,AXIS1=$(MYPVPREFIX)MOT:APERTURE,TOL=1000,LOOKUP=LOOKUPFILE1")

# Load the records which control closing the aperture
$(IFIOC_GALIL_01) dbLoadRecords("$(MOTOREXT)/db/loqAperture.db", "P=$(MYPVPREFIX), SETPTAXIS=$(MYPVPREFIX)LKUP:APERTURE:")
