#ifndef DATUM_H
#define DATUM_H

#include <string>

// The constructor for booleans is explicit, which means C++ cannot
// use the constructor to do automatic type conversions.
//
//      Datum d = new Datum(14);
//
// is a bug:  right side pointer to Datum, left side Datum.  But...
// C++ will convert pointers to booleans, and there IS a boolean
// constructor for Datum, so it creates a boolean true Datum.
// We'd rather get a compiler error then have things silently become
// something else.
// Maybe we should make the single-argument constructors explicit as
// well, but that hasn't seemed to be a problem.
//

class Datum {
public:
        Datum(const Datum &d);
        explicit Datum(int i);
        explicit Datum(bool b);
        explicit Datum(const char *s);
        explicit Datum(std::string s);

        bool isInt()     const;
        bool isBool()    const;
        bool isRString() const;

        Datum &operator= (const Datum &d);
        bool   operator==(Datum &d) const;
        bool   operator< (Datum &d) const;

        int         getInt()     const;
        bool        getBool()    const;
        std::string getRString() const;
        std::string toString()   const;

private:
        typedef enum { D_INT = 0, D_BOOL, D_RSTRING } datumty;

        datumty ty;

        int         idata;
        bool        bdata;
        std::string sdata;
};

#endif
