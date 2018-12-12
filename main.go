package main

import (
	"log"
	"os"
	"strconv"
)

var urls []string
var bucket string

// Loads other configuration variables from env vars
func loadConfig() {

	// Verify the bucket name
	bucket = os.Getenv("DATA_BUCKET")

	if len(bucket) > 0 {
		log.Println("DATA_BUCKET loaded as " + bucket)
	} else {
		log.Panicln("DATA_BUCKET not set. Exiting.")
	}

}

// Loads URLs from env vars `URL_1`, `URL_2`, etc, into the slice `urls`
func loadUrls() {
	// var i int = 1

	var checkNext bool = true
	var value string

	for i := 1; checkNext; i++ {

		var envvar string = "URL_" + strconv.Itoa(i)

		// Check if environment variable URL_{i} is set
		// If it exists, add it to the end of the slice, and check the next.
		// If it does not exist, do nothing with the current value, and stop checking for future values
		value = os.Getenv(envvar)

		if len(value) > 0 {
			log.Println(envvar + " loaded as " + value)
			urls = append(urls, value)
		} else if i == 1 {
			log.Panicln(envvar + " not found. No URLs found so can not continue.")
		} else {
			checkNext = false
		}

	}
}

func main() {
	log.Println("Starting remote file watcher")

	// Logging to stdout
	log.SetOutput(os.Stdout)

	// Read URLs
	loadUrls()

	// Read config from env vars
	loadConfig()

	log.Println(urls)

}
