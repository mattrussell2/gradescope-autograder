/**
 * Hashtable.h
 *
 *      Interface of Hashtable implmentation, using chaining. 
 *      Interface mostly follows std::unordered_map
 *
 * Kevin Destin
 * COMP15
 * Spring 2019
 *
 */
#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <string>
#include <vector>
/**
 * @brief A hashtable implementation
 *
 * Uses the roughly the same interface as std::unordered_map
 */
template <class Value>
class Hashtable {
public:
        typedef std::string Key;

        Hashtable();
        Hashtable(size_t tablesize);

        Value* insert(const Key& key, const Value&);
        Value* insert(const Key& key, const Value& toInsert, Value* hint);

        Value&       at(const Key& key);
        const Value& at(const Key& key) const;

        Value*       find(const Key& key);
        const Value* find(const Key& key) const;

        Value&       operator[](const Key& key);
        const Value& operator[](const Key& key) const;

        const Value* end() const;
        double       loadFactor() const;
        size_t       size() const;

private:
        /**
         * @brief A struct to store Hashtable elements as a Key-Value pair
         *
         */
        struct KeyValue {
                KeyValue(const Key& k, const Value& v) : key(k), val(v) {}
                Key   key;
                Value val;
        };

        void   expand();
        size_t indexOf(const Key&) const;

        static constexpr double            maxLoadFactor = 0.75;
        std::vector<std::vector<KeyValue>> table;
        size_t                             numElems = 0;
};

#endif
