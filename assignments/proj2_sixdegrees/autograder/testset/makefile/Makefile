CXX      = clang++
CXXFLAGS = -g3 -Wall -Wextra -std=c++14 -I .
TESTS    = $(shell bash -c "echo test{00..42}")
TESTDIR  = ../../testset/cpp

${TESTS}: CollabGraph.o Artist.o
	${CXX} ${CXXFLAGS}  -o $@ $^ ${TESTDIR}/$@.cpp

SixDegrees: main.o SixDegrees.o CollabGraph.o Artist.o
	${CXX} -o $@ $^

# Don't delete .o files
.SECONDARY:

%.o: %.cpp $(shell echo *.h)
	${CXX} ${CXXFLAGS} -c $<

clean:
	rm -rf test?? *.o SixDegrees
