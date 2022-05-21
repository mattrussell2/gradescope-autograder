/**
 * Hashtable.cpp
 *
 *      Implementation of Hashtable implmentation, using chaining. 
 *      Interface mostly follows std::unordered_map
 *
 * Kevin Destin
 * COMP15
 * Spring 2019
 *
 */
#include "Hashtable.h"
#include <algorithm>
#include <functional>
#include <iostream>

/**
 * @brief Default constructor. Initializes table with 1024 buckets
 */
template <class Value>
Hashtable<Value>::Hashtable() : Hashtable(1 << 19) {}

/**
 * @brief  Parameterized constructor. Initializes table with tablesize buckets
 *
 * @param tablesize
 */
template <class Value>
Hashtable<Value>::Hashtable(size_t tablesize) {
        table.resize(tablesize);
}

/**
 * @brief Inserts the Key Value pair into the hashtable
 *
 * @param key       Key associated with value to insert
 * @param toInsert  Value to insert to table
 * @return Value*   Pointer to inserted value
 */
template <class Value>
Value* Hashtable<Value>::insert(const Key& key, const Value& toInsert) {
        Value* hint = find(key);

        return insert(key, toInsert, hint);
}

/**
 * @brief Inserts the Key Value pair into the hashtable
 *
 * @param hint      A placement hint either updates an existing value, or
 *                  creates a new key value pair
 * @param key       Key associated with value to insert
 * @param toInsert  Value to insert to table
 * @return Value*   Pointer to inserted value
 */
template <class Value>
Value* Hashtable<Value>::insert(const Key& key, const Value& toInsert,
                                Value* hint) {
        Value* toReturn = hint;
        // Key already exists, so just update stored value
        if (toReturn != end())
                *toReturn = toInsert;
        else {
                if (loadFactor() > maxLoadFactor)
                        expand();
                // Insert a new KeyValue object  at the end of correct bucket
                table[indexOf(key)].emplace_back(key, toInsert);
                // Get address of inserted element.
                toReturn = &(table[indexOf(key)].back().val);
                numElems++;
        }

        return toReturn;
}

/**
 * @brief Doubles the size of the table
 */
template <class Value>
void Hashtable<Value>::expand() {
        //std::cerr << __func__ << ":" <<__LINE__ <<std::endl;
        // Make a new bigger table
        // Make the size of the new table coprime to the first
        Hashtable newTable(table.size() * 2 + 1);

        // Insert all keyvalue pairs from all the buckets in the old table in
        // the new table
        for (const std::vector<KeyValue>& bucket : table)
                for (const KeyValue& e : bucket)
                        newTable.insert(e.key, e.val);

        // Swap new table with old table.
        std::swap(*this, newTable);
}

/**
 * @brief Returns a reference to key's corresponding value in the table
 * @throws runtime_error if key is not in table
 * 
 * @param key 
 * @return Value& 
 */
template <class Value>
Value& Hashtable<Value>::at(const Key& key) {
        Value* toReturn = find(key);
        if (toReturn == end())
                throw std::runtime_error("Key not in table");
        return *toReturn;
}

template <class Value>
const Value& Hashtable<Value>::at(const Key& key) const {
        const Value* toReturn = find(key);
        if (toReturn == end())
                throw std::runtime_error("Key not in table");
        return *toReturn;
}

/**
 * @brief Checks if  table has a stored value for key
 *        Returns Hashtable<Value>::end() if not found.
 *
 * @tparam Value
 * @param key
 * @return const Value*
 */
template <class Value>
Value* Hashtable<Value>::find(const Key& key) {
        for (KeyValue& k : table[indexOf(key)])
                if (k.key == key)
                        return &(k.val);
        return nullptr;
}

template <class Value>
const Value* Hashtable<Value>::find(const Key& key) const {
        for (const KeyValue& k : table[indexOf(key)])
                if (k.key == key)
                        return &(k.val);
        return nullptr;
}

/**
 * @brief Gets value corresponding to provided key;
 *        If value doesn't exist, a default one is created and returned
 *        (Just like unordered_map::operator[])
 *
 * @param key
 * @return Value&
 */
template <class Value>
Value& Hashtable<Value>::operator[](const Key& key) {
        Value* element = find(key);
        if (element == end())
                return *insert(key, Value(), element);

        return *element;
}

/**
 * @brief Function to mimic std::unordered_set::end()
 *        Returns nullptr to signal invalid
 */
template <class Value>
const Value* Hashtable<Value>::end() const {
        return nullptr;
}

/**
 * @brief Computes the index of provided key
 *
 * @param key         The key
 * @return size_t The corresponding index of provided key
 */
template <class Value>
size_t Hashtable<Value>::indexOf(const Key& key) const {
        static std::hash<Key> hash_slinging_slasher;
        return hash_slinging_slasher(key) % table.size();
}

/**
 * @brief Returns number of elements stored in hashtable
 *
 * @return size_t
 */
template <class Value>
size_t Hashtable<Value>::size() const {
        return numElems;
}

/**
 * @brief Returns loadFactor of hashtable
 *
 * @tparam Value
 * @return double
 */
template <class Value>
double Hashtable<Value>::loadFactor() const {
        return (double)numElems / table.size();
}

#include "Entry.h"
// Explicit template specialization for "Entry"s
template class Hashtable<std::vector<Entry>>;
template class Hashtable<std::string>;
