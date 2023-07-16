# Testing Makefile
# Is run from the results/build/ directory
TESTSOURCEDIR=../../testset/cpp

CXX      = clang++
CXXFLAGS = -g3 -Wall -Wextra -std=c++14 -I .

TESTS=$(shell bash -c "echo test{01..58}")

${TESTS}:
	${CXX} ${CXXFLAGS} -o $@ $^ ${TESTSOURCEDIR}/$@.cpp

# Don't delete .o files
.SECONDARY:


%.o: %.cpp $(shell echo *.h)
	${CXX} ${CXXFLAGS} -c $<


# Don't delete .o files
.SECONDARY:

clean:
	rm -rf test?? *.o 