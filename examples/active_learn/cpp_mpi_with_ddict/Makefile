CC ?= gcc
CXX ?= g++
CFLAGS ?= -fPIC -Wall -O0 -g -fomit-frame-pointer
# -D_GLIBCXX_USE_CXX11_ABI=0
#CFLAGS ?= -g -O0 -DDRAGON_DEBUG -Wall

ifeq ($(VIRTUAL_ENV),)
	VIRTUAL_ENV = $(CONDA_PREFIX)
endif

ifeq ($(DRAGON_INCLUDE_DIR),)
    DRAGON_INCLUDE = $(shell dragon-config -o)
else
    DRAGON_INCLUDE = -I$(DRAGON_INCLUDE_DIR)
endif

ifeq ($(DRAGON_LIB_DIR),)
    DRAGON_LINK = $(shell  dragon-config -l)
else
    DRAGON_LINK = -L$(shell echo ${DRAGON_LIB_DIR}) -ldragon
endif

CFLAGS += $(DRAGON_INCLUDE) --std=c++20
LDFLAGS += $(DRAGON_LINK)

simulation: simulation.cpp
	$(CXX) $(CFLAGS) -o $@ $^ $(LDFLAGS)
