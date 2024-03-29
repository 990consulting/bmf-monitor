All files in this repository are copyright (c) 2019 Applied Nonprofit Research, LLC. All rights reserved.

File Watch and Fetcher

## AWS Deployment

No external dependencies required. Simply upload main.py.

## Local Usage
Designed for lambda, but can be run elsewhere. Configuration is entirely through environment variables due to being built for lambda first.

An example usage might look like:

```
DEBUG=1 ALERT_SNS_CHANNEL=alertchannel DATA_BUCKET=s3-bucket-name URL_1=http://example.com/file1.csv URL_2=http://example.com/file2.csv URL_3=http://example.com/file3.csv python3 main.py
```

## Docker Dev and Run

To build the container, run:

```
docker build -t app .
```

Rebuild should only be needed when dependencies in requirements.txt have changed.

Then, to run:

```
docker run \
 -v ${PWD}:/app \
 -e "DEBUG=1" \
 -e "ALERT_SNS_CHANNEL=test-channel" \
 -e "DATA_BUCKET=data-bucket-s3" \
 -e "URL_1=http://example.com/file1.csv" \
 -e "URL_2=http://example.com/file2.csv" \
 -e "URL_3=http://example.com/file3.csv" \
 app
```

This will set up the configuration, and with the -v command, mount the current code. Alternatively, you can omit the -v cmd, and rebuild on any code changes.

## Configuration

There are a number of environment variables used for configuration:

 * `DATA_BUCKET`
   * Enables verbose logging
   * required
   * example: "TBD"

 * `AWS_REGION`
   * Specifies the AWS region for SNS
   * required, if not using US Virginia
   * default: 'us-east-1'

 * `URL_1`, `URL_2`, `URL_3`, ... , `URL_n`
   * URLs to fetch. Create as many of these as needed for URLs. Will iterate over all
   * `URL_1` required, `URL_2` and beyond are optional
   * example: "http://example.com/file1.csv"

 * `DEBUG`
   * Enables verbose logging
   * default = false
   * example: "true"

  * `ALERT_SNS_CHANNEL`
    * SNS channel to send alerts to - will create channel if not existing
    * default = None
    * example: "tbd"

  * `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
    * AWS credentials if run outside lambda. Will also check ~/.aws/credentials as well

   TODO: Fill this example once format is decided

## IAM Role

TODO : provide more info here about the IAM role policies needed to succeed
https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example.html


## Specifications

deliverable: a developed lambda function, runnable on an automated schedule. Also full source code in client's
github account (repo @ gh:borenstein/bmf-monitor)

configuration vars:
 * `URL_1`, `URL_2`, etc.
   * URLs to fetch (set up the 4 at the beginning, but would parse an infinate number until it's found empty)
 * `DATA_BUCKET`
   * s3 bucket to dump results, and used to store hashes from previous checks as well
 * `ALERT_SNS_CHANNEL`
   * SNS channel to be sent messages on changes


https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf


On each run:

  Fetch all the files in `URL_n`.
  Fetch each's URL's previously known hash from s3

  If the hash differs, refetch all the files, store in s3 bucket in timestamped directory.
  Update hash file.
  Send notification email.
