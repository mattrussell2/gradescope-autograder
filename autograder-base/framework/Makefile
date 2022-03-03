# 	         Makefile for COMP 40 Homework 1
#
#     Author: Noah Mendelsohn (adapted from Norman Ramsey's compile script)
#
#  Maintenance targets:
#
#
#    all           - (default target) make sure everything's compiled
#    clean         - clean out all compiled object and executable files
# NEEDSWORK brightness and fgroups should be deleted when experiments done
#    forceleak	   - forces a memory leak that valgrind should catch
#    noleak        - allocates buffer on the stack, so it's cleaned before leaving
#    forceexitcode - exits with integer exit code specified on command line
#

# Executables to built using "make all"

EXECUTABLES = forceleak noleak forceexitcode

#
#  The following is a compromise. You MUST list all your .h files here.
#  If any .h file changes, all .c files will be recompiled. To do better,
#  we could make an explicit target for each .o, naming only the .h
#  files it really uses.
#
# Add your own .h files to the right side of the assingment below.

INCLUDES = fgroups.h duplines.h duplinesinput.h duplinesdata.h

# Do all C compies with gcc (at home you could try clang)
GCC = gcc

# Comp 40 directory

COMP40 = /comp/40

# the next two lines enable you to compile and link against CII40
CIIFLAGS = `pkg-config --cflags cii40`
CIILIBS = `pkg-config --libs cii40`

# the next three lines enable you to compile and link against course software
# -DLIST gives the list option of duplines NEEDSWORK
CFLAGS = -I. -I$(COMP40)/include $(CIIFLAGS) -DLIST
# NEEDSWORK: -lm below probably not needed
LIBS = $(CIILIBS) -lm    
LFLAGS = -L$(COMP40)/lib64

# these flags max out warnings and debug info
FLAGS = -g -O -Wall -Wextra -Werror -std=c99 -pedantic

# 
#    'make all' will build all executables
#
#    Note that "all" is the default target that make will build
#    if nothing is specifically requested
#
all: $(EXECUTABLES)

# 
#    'make clean' will remove all object and executable files
#
clean:
	rm -f $(EXECUTABLES) *.o *~ *.pyc core.* vgcore.*


# 
#    To get any .o, compile the corresponding .c
#
%.o:%.c $(INCLUDES)
	$(GCC) $(FLAGS) $(CFLAGS) -c $<

#
# Individual executables
#
#    Each executable depends on one or more .o files.
#    Those .o files are linked together to build the corresponding
#    executable.

noleak: noleak.o
	$(GCC) $(FLAGS) $(LFLAGS) -o noleak noleak.o

forceleak: forceleak.o
	$(GCC) $(FLAGS) $(LFLAGS) -o forceleak forceleak.o

forceexitcode: forceexitcode.o
	$(GCC) $(FLAGS) $(LFLAGS) -o forceexitcode forceexitcode.o

echo:
	echo "$(CIIFLAGS)"
