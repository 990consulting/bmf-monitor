File Watch and Fetcher

## Local Usage
Designed for lambda, but can be run elsewhere. Configuration is entirely through environment variables due to being built for lambda first.

An example usage might look like:

```
DEBUG=1 ALERT_EMAIL=jdoe@example.com DATA_BUCKET=1 URL_1=http://example.com/file1.csv URL_2=http://example.com/file2.csv URL_3=http://example.com/file3.csv python3 main.py
```

## Configuration

There are a number of environment variables used for configuration:

 * `DATA_BUCKET`
   * Enables verbose logging
   * required
   * example: "TBD" 

   TODO: Fill this example once format is decided

 * `URL_1`, `URL_2`, `URL_3`, ... , `URL_n`
   * URLs to fetch. Create as many of these as needed for URLs. Will iterate over all
   * `URL_1` required, `URL_2` and beyond are optional
   * example: "http://example.com/file1.csv"

 * `DEBUG`
   * Enables verbose logging
   * default = false
   * example: "true"


## Specifications

deliverable: a developed lambda function, runnable on an automated schedule. Also full source code in client's 
github account (repo @ gh:borenstein/bmf-monitor)

Cost, paid at completion: $250

configuration vars:
 * `URL_1`, `URL_2`, etc.
   * URLs to fetch (set up the 4 at the beginning, but would parse an infinate number until it's found empty)
 * `DATA_BUCKET`
   * s3 bucket to dump results, and used to store hashes from previous checks as well
 * `ALERT_EMAIL`
   * receives email on success


https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf


On each run:

  Fetch all the files in `URL_n`.
  Fetch each's URL's previously known hash from s3

  If the hash differs, refetch all the files, store in s3 bucket in timestamped directory.
  Update hash file.
  Send notification email.
