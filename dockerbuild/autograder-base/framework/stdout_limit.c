/*
 *                           stdout_limit.c
 *                      Author: Noah Mendelsohn
 *    
 *           Copies stdin to stdout, but only up to number of characters
 *           specified as the argument.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

const ssize_t BUFSIZE = 8192;

#define min(a,b) ((a)<(b) ? (a) : (b))

int main(int argc, char *argv[])
{
    char buf[BUFSIZE];
    ssize_t sz;
    ssize_t limit;

    char *ptr;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <max-stdout-size>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    /*
     * Get limit from arglist
     */
    limit = strtol(argv[1], &ptr, 10);

    /* Not really needed */
        for (int i = 0; i<sizeof(buf); i++) {
        buf[i] = 0;
    }
  
    
        
    /* 
     * Read into buffer, but no more than remaining limit 
     */
    while( (sz = read(STDIN_FILENO, buf, min(limit, sizeof(buf)))) > 0) {
        /* Read successful */
        write(STDOUT_FILENO, buf, sz);
        limit -= sz;               /* reduce limit by amount read */
    }

    /*
     * Handle errors reading
     */
    close(STDOUT_FILENO);
    close(STDIN_FILENO);
    if (sz < 0) {
        perror("sizelimit error reading stdin");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}

