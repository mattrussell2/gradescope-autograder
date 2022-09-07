# Testing Makefile
# Is run from the results/build/ directory
TESTSOURCEDIR=../../testset/cpp

CXX      = clang++
CXXFLAGS = -g3 -Wall -Wextra -std=c++14 -I .


mem_test: mem_test.o
	$(CXX) -o $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $<

# Don't delete .o files
.SECONDARY:

clean:
	rm -rf test?? *.o 