epicsEnvSet "LOOKUPFILE1" "$(ICPCONFIGROOT)/motionSetPoints/aperture.txt"

motionSetPointsConfigure("LOOKUPFILE1","LOOKUPFILE1")

$(IFIOC_GALIL_01) dbLoadRecords("$(MOTIONSETPOINTS)/db/motionSetPoints.db","P=$(MYPVPREFIX)LKUP:APERTURE:,NAME1=APERTURE,AXIS1=$(MYPVPREFIX)MOT:APERTURE,LOOKUP=LOOKUPFILE1")

# Load the records which control closing the aperture
$(IFIOC_GALIL_01) dbLoadRecords("$(MOTOREXT)/db/loqAperture.db", "P=$(MYPVPREFIX), SETPTAXIS=$(MYPVPREFIX)LKUP:APERTURE:")
