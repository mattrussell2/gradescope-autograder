/**
 ** Artist.h
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

#ifndef __ARTIST__
#define __ARTIST__

#include <iostream>
#include <string>
#include <vector>

class Artist {

public:

    /* Constructors */
    Artist();
    Artist(const std::string &name);

    /* copy constructor/assignment */
    Artist(const Artist &source);
    Artist &operator=(const Artist &rhs);

    /* move constructor/assignment */
    Artist(Artist &&source);
    Artist &operator=(Artist &&rhs);

    /* Mutators */
    void add_song(const std::string &song);
    void set_name(const std::string &name);

    /* Accessors */
    std::string get_name() const;
    bool        in_song(const std::string &song) const;
    std::string get_collaboration(const Artist &artist) const;
    
    
    /* friend functions */
    friend bool           operator == (const Artist &a1, const Artist &a2);
    friend bool           operator != (const Artist &a1, const Artist &a2);
    friend std::ostream & operator << (std::ostream &out,
                                       const Artist &artist);

private:
    std::string name;
    std::vector<std::string> discography;
};

#endif /* __ARTIST__ */
