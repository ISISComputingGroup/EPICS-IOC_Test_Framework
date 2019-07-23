$(IFIOC_GALIL_01=#) dbLoadRecords("$(JAWS)/db/split_jaws_header_vertical.db","P=$(MYPVPREFIX)MOT:,JAWS=JAWS1:,mXN=MTR0101,mXS=MTR0102,mXW=MTR0202,mXE=MTR0201")

$(IFIOC_GALIL_02=#) dbLoadRecords("$(JAWS)/db/split_jaws_horizontal.db","P=$(MYPVPREFIX)MOT:,JAWS=JAWS1:,mXW=MTR0202,mXE=MTR0201")
