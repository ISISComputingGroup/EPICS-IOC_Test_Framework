GalilCreateController("Galil1", "$(GALILADDR1)", 20)

GalilCreateAxis("Galil1","A",1,"",1)
GalilCreateAxis("Galil1","B",1,"",1)
GalilCreateAxis("Galil1","C",1,"",1)
GalilCreateAxis("Galil1","D",1,"",1)
GalilCreateAxis("Galil1","E",1,"",1)
GalilCreateAxis("Galil1","F",1,"",1)
GalilCreateAxis("Galil1","G",1,"",1)
GalilCreateAxis("Galil1","H",1,"",1)

$(IFNEWGALIL=#) GalilCreateCSAxes("Galil1")

epicsEnvSet "HOME_HEADER" "$(GALIL)/gmc/galil_Default_Header.gmc"
epicsEnvSet "HOME_MODE_1" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_MODE_2" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_MODE_3" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_MODE_4" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_MODE_5" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_MODE_6" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_MODE_7" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_MODE_8" "$(GALIL)/gmc/galil_Home_No_Home.gmc"
epicsEnvSet "HOME_FOOTER" "$(GALIL)/gmc/galil_Default_Footer.gmc"

GalilStartController("Galil1","$(HOME_HEADER);$(HOME_MODE_1)!$(HOME_MODE_2)!$(HOME_MODE_3)!$(HOME_MODE_4)!$(HOME_MODE_5)!$(HOME_MODE_6)!$(HOME_MODE_7)!$(HOME_MODE_8);$(HOME_FOOTER)",0,0,3)

$(IFNEWGALIL=#) GalilCreateProfile("Galil1", 2000)

# Ensure there is a newline at the end of the file!
