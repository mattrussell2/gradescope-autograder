#include <stdlib.h>
#include <stdio.h>

int
main(int argc, char *argv[])
{
	if (argc != 2) {
		fprintf(stderr, "Usage: %s <exitcodeinteger>\n", argv[0]);
		exit(1);
	}
       
	exit(atoi(argv[1]));
}
