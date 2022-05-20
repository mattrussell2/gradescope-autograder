#########################################################
#                   HOMEWORK 1: LISTS                   #
# by C.R. Calabrese, Jan-Feb 2021                       #
#########################################################

CXX = clang++
CXXFLAGS = -g3 -Wall -Wextra -Wpedantic -Wshadow
LDFLAGS  = -g3

default: unit_test

# this rule will run unit_test while compiling both
# CharArrayList and CharLinkedList
unit_test: testCharArrayList.o CharArrayList.o
	$(CXX) testCharArrayList.o  CharArrayList.o -o unit_test

testCharArrayList.o: testCharArrayList.cpp
	$(CXX) $(CXXFLAGS) -c testCharArrayList.cpp

CharArrayList.o: CharArrayList.cpp
	$(CXX) $(CXXFLAGS) -c CharArrayList.cpp

# remove executables and object code from the current folder -- the
# executable created by unit_test is called a.out
clean:
	rm *.o unit_test

