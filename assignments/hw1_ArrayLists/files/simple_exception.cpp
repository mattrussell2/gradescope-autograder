/*
 * Here's how you can throw an exception.  There's a lot more one can
 * learn about exceptions, but this has basic examples.  In C++, you
 * "throw" an exception, and you can give "throw" any type of value.
 * There are some built-in classes that represent exceptions, and
 * it's a good idea to use them when they make sense (ex: if an index
 * is out of range, it would make sense to throw range_error). 
 *
 * We call the exception constructors with a string that represents 
 * the message associated with the error.
 *
 * Programs can choose to handle exceptions using a "try" statement,
 * but if they don't, the program will terminate with an unhandled
 * exception, and the message will print out.
 *
 * For no good reason, the first example also demonstrates a more 
 * obscure feature of C++: if you put two string constants one after 
 * the other in a source file with no intervening operator, the 
 * strings are concatenated together to make one string constant.  It
 * can be handy if you have to spread a string constant across 
 * multiple lines, e. g., if the string is very long (like a URL).
 *
 * Mark A. Sheldon, Tufts University, Fall 2015
 * Additional example and comments added by Cicely Panara, Fall 2020
 */

#include <iostream>
#include <string>
#include <stdexcept>

using namespace std;


/* Functions */
void program_execution();
int crash();                   /* example of a runtime error */


void throw_catch();
void assert_in_range(int num); /* example of a range error */
int divide_by_num(int num);    /* example of a caught logic error */



/* A driver that demonstrates how exceptions work    
 * 
 * The first function call shows how execution is impacted by an
 * error being thrown.
 *
 * the second function call shows error throwing and catching.   
 *                                                         
 * NOTE: make sure you comment out the first function if you
 *       want to see the example of throwing and catching.     
 */
int main()
{
    program_execution(); /* comment this out after running once! */
    throw_catch();
    return 0;
}



/******************************************************************
 *                                                                *
 *                       Program Execution                        *
 *                                                                *
 ******************************************************************/


/*
 * Simple function that demonstrates how a runtime error will 
 * interfere with program execution. 
 * 
 * Note: terminates with a runtime error
 */
void program_execution()
{
        cout << "Result:  " << crash() << endl;
        cout << "This won't print" << endl;
}


/*
 * Purpose: simple crash function that throws a runtime error
 *          with the message "Crashing!  oh no!"
 * Notes: function will cause program to exit,
 *        the type of error thrown is std::runtime_error,
 *        the return statement does not run - the error interrupts
 *        and the program exits there
 */
int crash()
{
        throw runtime_error("Crashing!"
                            "  oh no!");
        return 12;
}


/******************************************************************
 *                                                                *
 *                  Throwing and Handling Errors                  *
 *                                                                *
 ******************************************************************/


/* Simple example to demonstrate error throwing and catching.
 * Suggested use: 
 *         run entering a value in the range of 1-10
 *         run entering a value outside the range 1-10, but not 0
 *         run entering 0
 */
void throw_catch() 
{
    int response;
    cout << "Enter a value between 0 and 10\n";
    cin >> response;

    /* the try statement essentially says "try to do this thing,   *
     * it might get interrupted by an error"                       *
     * the catch statement under it says what to do if the given   *
     * type of error (logic_error) is encountered in the try block */
    try { 
        assert_in_range(response);
        int result = divide_by_num(response);
        cout << "100 divided by your number is " << result 
             << endl;
    } 
    catch (logic_error) {
        cout << "you can't divide by zero\n"; 
    }

    cout << "congratulations! your number was in range!" << endl;
}


/* Purpose: ensure a passed number is in the desired range (0-10), 
 *          demonstrate how an exception might be thrown
 * Parameters: num - the number to ensure the range for
 * Notes: if the passed number is out of range, a range_error exception is
 *        thrown
 */
void assert_in_range(int num)
{
    if (num < 0 or num > 10) {
        throw range_error("your number was not between 1 and 10!");
    }
}


/* Purpose: divide 100 by the passed number, give an example of
 *          a caught exception
 * Parameters: num - the number to divide 100 by
 * Returns: an integer representing the result of the division
 * Notes: if 0 is passed, a logic error is thrown
 */
int divide_by_num(int num)
{
    if (num == 0) {
        throw logic_error("dividing by zero");
    }
    return 100 / num;
}

