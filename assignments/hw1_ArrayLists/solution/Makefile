# Makefile for HW1: ArrayList
# Matt Russell
# 
# This Makefile will build unit_test for the unit_testing 
# framework.

CXX=clang++
CXXFLAGS=-Wall -Wextra -Wpedantic -Wshadow

unit_test: unit_test_driver.o CharArrayList.o
	${CXX} unit_test_driver.o CharArrayList.o

CharArrayList.o: CharArrayList.cpp CharArrayList.h
	${CXX} ${CXXFLAGS} -c CharArrayList.cpp

clean: 
	rm *.o a.out *~ *#