# Testing Makefile
# Is run from the submission directory
TESTSETDIR=../../testset
TESTSOURCEDIR=${TESTSETDIR}/cpp


CXX      = clang++
CXXFLAGS = -g3 -Wall -Wextra -std=c++14 -I .


ARRAYLISTTESTS=$(shell bash -c "echo test{01..57}")

${ARRAYLISTTESTS}: CharArrayList.o
	${CXX} ${CXXFLAGS}  -o $@ $^ ${TESTSOURCEDIR}/$@.cpp


# Don't delete .o files
.SECONDARY:


%.o: %.cpp $(shell echo *.h)
	${CXX} ${CXXFLAGS} -c $<

clean:
	rm -rf test?? *.o *.dSYM
