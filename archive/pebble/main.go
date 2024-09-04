package main

import (
	"fmt"
	"log"
	"strings"

	"github.com/cockroachdb/cockroach/pkg/storage"
	"github.com/cockroachdb/pebble"
)

func main() {
	DIR := "/home/xiaochen/data/cockroachdb-data"
	// DIR := "./demo"

	opts := storage.DefaultPebbleOptions()

	db, err := pebble.Open(DIR, opts)
	if err != nil {
		log.Fatal(err)
	}

	// write api:
	// batch := db.NewBatch()
	// batch.Set()
	// batch.SetDeferred()
	// batch.SetRepr()
	// db.NewBatchWithSize()
	// db.NewIndexedBatch()
	// db.NewIndexedBatchWithSize()
	// db.Set()

	if false {
		key := []byte("hello")
		if err := db.Set(key, []byte("world"), pebble.Sync); err != nil {
			log.Fatal(err)
		}
		value, closer, err := db.Get(key)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%s %s\n", key, value)
		if err := closer.Close(); err != nil {
			log.Fatal(err)
		}
	}

	if true {
		snapshot := db.NewSnapshot()

		iter, err := snapshot.NewIter(nil)
		if err != nil {
			log.Fatal(err)
		}

		valid := iter.First()
		if !valid {
			log.Fatal("invalid: iter.First()")
		}

		count := 0
		for valid {
			count++

			key := iter.Key()
			value := iter.Value()

			kStr := safeString(key)
			vStr := safeString(value)

			if strings.Contains(vStr, "xiaochen_debug_insert") {
				if len(vStr) < 100 {
					fmt.Printf("[%d] key: %s, value: %s\n", count, kStr, vStr)
				}
			}

			valid = iter.Next()

			// break
		}
		if err := iter.Close(); err != nil {
			log.Fatal(err)
		}

		if err := snapshot.Close(); err != nil {
			log.Fatal(err)
		}
	}

	if err := db.Close(); err != nil {
		log.Fatal(err)
	}
}

// Return the string representation of the byte slice, only valid ASCII characters
// and symbols are allowed. Other characters are printed in hex format.
func safeString(bs []byte) string {
	s := ""
	for _, b := range bs {
		if b < 32 || b > 126 {
			s += fmt.Sprintf("\\x%02x", b)
		} else {
			s += string(b)
		}
	}
	return s
}
