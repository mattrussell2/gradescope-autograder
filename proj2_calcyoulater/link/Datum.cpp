#include <stdexcept>

#include "Datum.h"

using namespace std;

Datum::Datum(const Datum &d) : ty(d.ty) {
    switch (ty) {
        case D_INT:     idata = d.idata; break;
        case D_BOOL:    bdata = d.bdata; break;
        case D_RSTRING: sdata = d.sdata; break;
    }
}
Datum::Datum(int i)         : ty(D_INT),     idata(i) {}
Datum::Datum(bool b)        : ty(D_BOOL),    bdata(b) {}
Datum::Datum(const char *s) : ty(D_RSTRING), sdata(s) {}
Datum::Datum(string s)      : ty(D_RSTRING), sdata(s) {}

bool Datum::isInt()     const { return ty == D_INT; }
bool Datum::isBool()    const { return ty == D_BOOL; }
bool Datum::isRString() const { return ty == D_RSTRING; }

Datum &Datum::operator=(const Datum &d) {
    if (this == &d)     // Do nothing on self assignment
        return *this;
    
    ty = d.ty;
    switch (ty) {
        case D_INT:     idata = d.getInt();     break;
        case D_BOOL:    bdata = d.getBool();    break;
        case D_RSTRING: sdata = d.getRString(); break;
    }

    return *this;
}

bool Datum::operator==(Datum &d) const {
    /* Allow comparison of non-same types. */
    if (ty != d.ty) return false;

    switch (ty) {
        case D_INT:     return idata == d.getInt();
        case D_BOOL:    return bdata == d.getBool();
        case D_RSTRING: return sdata == d.getRString();
        default: return false;
    }
}

bool Datum::operator<(Datum &d) const {
    switch (ty) {
        case D_INT: return idata < d.getInt();
        default: throw runtime_error("datum_not_int");
    }
}

int Datum::getInt() const {
    if (ty != D_INT) throw runtime_error("datum_not_int");
    return idata;
}

bool Datum::getBool() const {
    if (ty != D_BOOL) throw runtime_error("datum_not_bool");
    return bdata;
}

string Datum::getRString() const {
    if (ty != D_RSTRING) throw runtime_error("datum_not_rstring");
    return sdata;
}

string Datum::toString() const {
    switch (ty) {
        case D_INT:     return std::to_string(idata);
        case D_BOOL:    return bdata ? "#t" : "#f";
        case D_RSTRING: return sdata;
        default: throw runtime_error("invalid_type");
    }
}
