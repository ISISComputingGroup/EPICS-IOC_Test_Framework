############ GEM jaws ##############
# Create a soft motor record on top of a normal motor record which allow the gap to be set for the motor

$(IFIOC_GALIL_02=#) dbLoadRecords("$(JAWS)/db/jaws.db","P=$(MYPVPREFIX)MOT:,JAWS=JAWS1:,mXN=MTR0202, mXS=MTR0201,mXW=MTR0204,mXE=MTR0203,IFINIT_FROM_AS=$(IFINIT_JAWS_FROM_AS=#),IFNOTINIT_FROM_AS=$(IFNOTINIT_JAWS_FROM_AS=)")
