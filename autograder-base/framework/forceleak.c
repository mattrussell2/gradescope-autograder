#include <stdlib.h>
#include <stdio.h>

#define SIZE 1000
int
main(int argc, char *argv[])
{
	char *buffer = malloc(SIZE);

	printf("Buffer of size %u malloc'd at address %p, not freeing!\n",
	       SIZE, buffer);

	buffer = NULL;

	exit(EXIT_SUCCESS);
}
