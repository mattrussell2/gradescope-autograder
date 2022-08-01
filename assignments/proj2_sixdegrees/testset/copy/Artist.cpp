/**
 ** Artist.cpp
 **
 ** Project Two: Six Degrees of Collaboration
 **
 ** Purpose:
 **   Represent an artist (musician), storing their name and
 **   and discography. Accessor and mutator functions are provided,
 **   and two artists can be compared in several ways.
 **
 ** ChangeLog:
 **   13 Nov 2020: rgilk01, jdavid07
 **     Adapted from 'Six Degrees of Kevin Bacon'
 **
 **   17 Nov 2020: zgolds01
 **     Refactored for concision & clarity, updated documentation
 **/


#include <iostream>
#include <vector>

#include "Artist.h"





/*********************************************************************
 ******************** public function definitions ********************
 *********************************************************************/



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: nullary constructor
 * @purpose: initialize an Artist instance
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: none
 */
Artist::Artist()
{
    name = "";
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: parameterized constructor
 * @purpose: initialize an Artist instance with a name
 *
 * @preconditions: none
 * @postconditions: the created Artist instance will have the provided name
 *
 * @parameters: a const std::string reference, the name of the Artist instance
 */
Artist::Artist(const std::string &name)
{
    this->name = name;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: add_song
 * @purpose: include another song in the discography of this Artist instance
 *
 * @preconditions: none
 * @postconditions: the provided song is added to the discography of this
 *                  Artist instance
 *
 * @parameters: a const std::string reference, the name of the song
 *              to be added
 * @returns: none
 */
void Artist::add_song(const std::string &song)
{
    discography.push_back(song);
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: set_name
 * @purpose: set the name of this Artist instance
 *
 * @preconditions: none
 * @postconditions: the name of this Artist instance is set to be the
 *                  provided std::string'n'
 *
 * @parameters: a const std::string reference, the new name of
 *              this Artist instance
 * @returns: a std::string, the name of this Artist instance 
 */
void Artist::set_name(const std::string &name)
{
    this->name = name;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: get_name
 * @purpose: retrieve the name of this Artist instance
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: none
 * @returns: a std::string, the name of this Artist instance 
 */
std::string Artist::get_name() const
{
    return name;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: in_song
 * @purpose: determine whether this Artist instance collaborated in
 *           a given song
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: a const std::string reference, the name of a song
 * @returns: a bool, true iff this Artist instance collaborates in the
 *           provided song
 */
bool Artist::in_song(const std::string &song) const
{
    for (std::size_t i = 0; i < discography.size(); i++) {
        if (discography.at(i) == song) {
            return true;
        }
    }

    /* If the song is not present in discography, then return false */
    return false;
}


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: get_collaboration
 * @purpose: determine whether this Artist instance collaborated with
 *           the given 'artist'
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: a const Artist reference, another artist
 * @returns: a std::string, the name of a song in which this Artist instance
 *           collaborates with the provided 'artist' (the empty string
 *           represents no collabortion between this instance and 'artist')
 */
std::string Artist::get_collaboration(const Artist &artist) const
{
    for (std::string song : discography) {
        if (artist.in_song(song)) {
            return song;
        }
    }

    /* The empty string represents no collaboration
     * between this instance and the the provided 'artist'
     */
    return "";
}





/*********************************************************************
 ******************** friend function definitions ********************
 *********************************************************************/



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: equal-to operator overload
 * @purpose: determine whether two Artist instances are equal
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: 1) a const Artist reference
 *              2) another const Artist reference
 * @returns: a bool, true iff the name of the Artist instances are the same
 */
bool operator==(const Artist &a1, const Artist &a2)
{
    return a1.name == a2.name;
}



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: not-equal-to operator overload
 * @purpose: determine whether two Artist instances are equal
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: 1) a const Artist reference
 *              2) another const Artist reference
 * @returns: a bool, true iff the name of the Artist instances are the same
 */
bool operator!=(const Artist &a1, const Artist &a2)
{
    return a1.name != a2.name;   
}


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: stream-insertion operator overload
 * @purpose: send the name of the provided 'artist' to the provided
 *           output stream
 *
 * @preconditions: none
 * @postconditions: none
 *
 * @parameters: 1) a std::ostream reference, where output is sent
 *              2) a const Artist reference, 
 * @returns: the modified output stream
 */
std::ostream &operator<<(std::ostream &out, const Artist &artist)
{
    out << artist.name;
    return out; 
}





/****************************************************************************
*****************************************************************************
*****************************************************************************
*****                        _______________  ____  __                  *****
*****                       / ___/_  __/ __ \/ __ \/ /                  *****
*****                       \__ \ / / / / / / /_/ / /                   *****
*****                      ___/ // / / /_/ / ____/_/                    *****
*****                     /____//_/  \____/_/   (_)                     *****
*****                                                                   *****
*****                       Don't keep scrolling :)                     *****
*****************************************************************************
*****************************************************************************
*****************************************************************************/















/* ...you kept scrolling?
 *
 * Well, don't say we didn't warn you.
 *
 * Below are four function definitions. They are implemented for two reasons:
 *   1) they grant you greater flexibilty in your implementation (i.e. you
 *      can safely pass around const Artist references)
 *   2) they allow for significant compilation optimization, which
 *      dramatically reduces the runtime of the project implementation
 *
 * These functions may seem intimidating to C++ programmers who have not yet
 * learned about 'The Big Five', and you don't need to understand these
 * functions to successfully implement the project, so we hid them down here.
 */



/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: copy constructor
 * @purpose: initialize an Artist instance from another Artist instace
 *
 * @preconditions: none
 * @postconditions: the created Artist instance is a copy of the proivded
 *                  source
 *
 * @parameters: a const Artist reference
 */
Artist::Artist(const Artist &source)
{
    *this = source;
}

/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: copy-assignment overload
 * @purpose: allow Artist instances to be set equal to each other
 *
 * @preconditions: none
 * @postconditions: the created Artist instance will be a deep copy of the
 *                  provided source
 * @parameters: a const Artist reference
 */
Artist &Artist::operator=(const Artist &rhs)
{
    if (this == &rhs) return *this;

    name = rhs.name;
    discography = rhs.discography;

    return *this;
}

/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: move constructor
 * @purpose: efficiently initialize an Artist instance from another
 *           Artist instance
 *
 * @preconditions: none
 * @postconditions: the created Artist instance is a copy of the provided
 *                  source
 *
 * @parameters: an Artist rvalue reference
 */
Artist::Artist(Artist &&source)
{
    *this = source;
}


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * @function: move-assignment operator overload
 * @purpose: efficiently initialize an Artist instance from another
 *           Artist instance
 *
 * @preconditions: none
 * @postconditions: the created Artist instance is a copy of the provided
 *                  source
 *
 * @parameters: an Artist rvalue reference
 */
Artist &Artist::operator=(Artist &&rhs)
{
    name = rhs.name;
    discography = rhs.discography;

    return *this;
}
