CXX = clang++
CXXFLAGS = -O2 -g3 -Wall -Wextra -std=c++11
DEFINE=s2019
gerp: main.o Index.o FSTree.o DirNode.o Hashtable.o
	$(CXX) -o $@ $^

%.o: %.cpp $(shell echo *.h)
	$(CXX) $(CXXFLAGS) -c $< -D${DEFINE}

testing:
	make clean && make DEFINE=TESTING_WITH_2018f gerp && /bin/time \
	./prepare.sh && make clean gerp
clean:
	rm -rf Index.o main.o Hashtable.o gerp *.dSYM
