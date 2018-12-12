File Watch and Fetcher

deliverable: a developed lambda function, runnable on an automated schedule. Also full source code in client's 
github account (repo @ gh:borenstein/bmf-monitor)

Cost, paid at completion: $250

configuration vars:
 * `URL_1`, `URL_2`, etc.
   * URLs to fetch (set up the 4 at the beginning, but would parse an infinate number until it's found empty)
 * `DATA_BUCKET`
   * s3 bucket to dump results, and used to store hashes from previous checks as well
 * `HASH_TYPE`
   * options: md5, sha1, sha256



https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf


On each run:

  Fetch all the files in `URL_n`.
  Fetch each's URL's previously known hash from s3

  If the hash differs, refetch all the files, store in s3 bucket in timestamped directory.
  Update hash file.
