# Testing Makefile
# Is run from the submission directory
TESTSETDIR=../../source
TESTSOURCEDIR=${TESTSETDIR}/cpp


CXX      = clang++
CXXFLAGS = -g3 -Wall -Wextra -std=c++14 -I .


ARRAYLISTTESTS=$(shell bash -c "echo test{01..60}")
# EXTRA_AL=$(shell bash -c "echo extraAL{01..03}")
# LINKEDLISTTESTS=$(shell bash -c "echo test{43..84}")
# EXTRA_LL=$(shell bash -c "echo extraLL{01..03}")


${ARRAYLISTTESTS}: CharArrayList.o
	${CXX} ${CXXFLAGS}  -o $@ $^ $@.cpp

# ${EXTRA_AL}: CharArrayList.o
# 	${CXX} ${CXXFLAGS}  -o $@ $^ ${TESTSOURCEDIR}/$@.cpp

# ${LINKEDLISTTESTS}: CharLinkedList.o
# 	${CXX} ${CXXFLAGS}  -o $@ $^ ${TESTSOURCEDIR}/$@.cpp

# ${EXTRA_LL}: CharLinkedList.o
# 	${CXX} ${CXXFLAGS}  -o $@ $^ ${TESTSOURCEDIR}/$@.cpp




# Don't delete .o files
.SECONDARY:


%.o: %.cpp $(shell echo *.h)
	${CXX} ${CXXFLAGS} -c $<

clean:
	rm -rf test?? *.o *.dSYM
