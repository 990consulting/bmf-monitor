#!/usr/bin/env python3

# =============================================================================
#     Program:  BMF Monitor
# Description:  Checks remote file URLs and fetches them if they have changed
#
#      Author:  Ben Yanke <ben@benyanke.com>
#        repo:  github:borenstein/bmf-monitor
#
# =============================================================================

import os
import time
import datetime
import boto3
import hashlib
from botocore.vendored import requests

# from botocore.exceptions import ClientError

class FileFetcher:
    # Bucket for data and hash storage
    data_bucket = None

    # URLs to check
    urls = []

    # Alerting sns channel
    alert_sns_channel = None

    # Set this to true by using env var DEBUG
    debug = None

    # Hard coded confg options
    bucket_path_hashes = None
    bucket_path_data = None

    # boto client handles
    s3 = None
    sns = None

    # Default region, override with env AWS_REGION
    aws_region = 'us-east-1'

    # Constructor
    def __init__(self):

        # Parses the env vars into the config vars
        self.load_config()

        # Setup the s3 handler
        self.s3 = boto3.resource('s3')

        # Setup the sns handler
        self.sns = boto3.client(
            'sns',
            region_name=self.aws_region
        )

        # Set the bucket paths
        self.bucket_path_hashes = "hashes"
        self.bucket_path_data = "files/" + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')

        # Fetch past hashes for comparison to present
        self.load_known_hashes_from_s3()

        # Fetch all URLs to check for change
        self.check_urls()

        # Check if pages have changed or not and handle
        if self.have_pages_changed():

            # stores in a new timestamp directory
            self.store_new_page_versions()

            self.log_info("Pages have changed - triggering change actions")

            # Send an SNS alert
            self.send_change_alert()

        else:
            self.log_info("No pages have changed - no further action required")

        self.log_info("Exiting successfully")

    ########################
    # Logging Methods
    ########################

    # Generic method to handle all log levels
    def log_write(self, level, msg):
        # Don't print debug out of debug mode
        if level is not 'debug' or self.debug:
            # flush=true means that the log messages are never buffered
            print("[" + self.log_time() + "] [" + level.upper() + "] " + str(msg), flush=True)

    # lturn a string with the timestamp for consistent logging purposes
    @staticmethod
    def log_time():
        return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    # Function to write an debug log
    # This method used in the main program
    def log_debug(self, msg):
        self.log_write('debug', msg)

    # Function to write an info log
    # This method used in the main program
    def log_info(self, msg):
        self.log_write('info ', msg)

    # Function to write a fatal log and exit w/ code 1
    # This method used in the main program to
    def log_fatal(self, msg):
        self.log_write('fatal', msg)
        exit(1)

    ########################
    # Main Methods
    ########################

    # Loads and verifies the configuration from environment variables
    def load_config(self):

        # Check for debug mode
        if "DEBUG" in os.environ and (os.environ['DEBUG'].lower() in ['1', 'true', 'yes', 'on']):
            self.debug = True
            self.log_debug("Debug mode enabled")

        self.log_info("Loading configuration")

        # Check if DATA_BUCKET is set
        # If not, fail hard. Can not run with a default
        if "DATA_BUCKET" in os.environ:
            self.data_bucket = os.environ['DATA_BUCKET']
            self.log_debug("data_bucket set to '" + self.data_bucket + "' with environment variable 'DATA_BUCKET'")
        else:
            self.log_fatal("Environment variable 'DATA_BUCKET' is not set")

        # Check if ALERT_SNS_CHANNEL is set
        # If not, fail to empty. Can still run without an alerting email
        if "ALERT_SNS_CHANNEL" in os.environ:
            self.alert_sns_channel = os.environ['ALERT_SNS_CHANNEL']
            self.log_debug(
                "alert_sns_channel set to '" + self.alert_sns_channel + "' with environment variable 'ALERT_SNS_CHANNEL'")
        else:
            self.log_debug("Environment variable 'ALERT_SNS_CHANNEL' is not set. Defaulting to blank.")

        # Check for aws region override - default set above
        if "AWS_REGION" in os.environ:
            self.aws_region = os.environ['AWS_REGION']

        self.log_info("Region set to " + self.aws_region)

        # Parse in URLs
        # Read in as many as exist, but fail hard if the first is not found. Can not run with a default
        # Will read in environment variables URL_1, URL_2, URL_3, ..., URL_n into list 'self.urls'
        #
        # Hard fails if at least URL_1 not set

        i = 1
        while True:
            varname = "URL_" + str(i)
            if varname in os.environ and len(os.environ[varname]) > 2:
                self.urls.append({
                    "url": os.environ[varname],
                    "stored_sha256": '',  # to be filled later
                    "current_sha256": '',  # to be filled later
                })
                self.log_debug("Environment variable '" + varname + "' set to " + os.environ[varname])
            else:
                # Hard fail if on the first loop
                if (i == 1):
                    self.log_fatal("URL_1 was not found - can not continue without at least one URL")
                # Otherwise, simply exit the loop, since we've parsed all the entries
                else:
                    self.log_info("Parsed " + str(len(self.urls)) + " URLs into the configuration")
                    break
            i += 1

        self.log_debug("Confguration successfully loaded")

    # Loads old known hashes from s3 bucket to check for changes
    def load_known_hashes_from_s3(self):

        self.log_debug("Loading previously known hashes from s3")

        # Loop through all URLs
        i = 1
        for url in self.urls:
            # Find the paths within the bucket to the files
            hash_filepath = self.bucket_path_hashes + '/url_' + str(i) + ".sha256"
            body_filepath = self.bucket_path_data + '/url_' + str(i) + ".txt"

            # Try/except handles when the file doesn't exist
            # store the file handle with the URL record for later writing
            url['hash_file_handle'] = self.s3.Object(self.data_bucket, hash_filepath)
            url['body_file_handle'] = self.s3.Object(self.data_bucket, body_filepath)

            try:
                url['stored_sha256'] = url['hash_file_handle'].get()['Body'].read().decode('utf-8')
                self.log_debug("File " + hash_filepath + " found in bucket " + self.data_bucket + " - hash : " + url[
                    'stored_sha256'])

            except self.s3.meta.client.exceptions.NoSuchKey:
                self.log_info(
                    "File " + hash_filepath + " not found in bucket " + self.data_bucket + " - assuming blank hash and writing blank file")

                # Write blank file for future writing
                url['hash_file_handle'].put(Body=b'')

                # Put blank value in data array to blank
                url['stored_sha256'] = ''

            i += 1

    # Checks all the URLs
    def check_urls(self):
        self.log_debug("Checking URLs against previously known hashes")

        # Loop through all URLs
        i = 1
        for url in self.urls:

            r = requests.get(url['url'], allow_redirects=True, timeout=5)

            # Only continue handling if it was a 200
            if r.status_code != 200:
                self.log_info("URL_" + str(i) + " returned HTTP code of " + str(r.status_code) + " - skipping")
                i += 1

                # Write hash blank for change detection, don't clear body so that
                # we still have it in event of a brief client-side outage
                url['hash_file_handle'].put(Body='')
                continue

            # Calculate page hash
            hashContent = str(r.text).encode('utf-8')

            sha256 = hashlib.sha256(hashContent).hexdigest()
            self.log_debug("URL_" + str(i) + " returned HTTP code of " + str(r.status_code))
            self.log_info("URL_" + str(i) + " sha256 = " + sha256)

            # Store to data array
            url['current_sha256'] = sha256

            # Write hash and content to s3 bucket as well
            url['hash_file_handle'].put(Body=sha256)
            url['content'] = r.text

            i += 1

    # Compares the past and current page hash to see if any pages have changed
    # returns bool, true means pages have changed, false means pages are the same
    def have_pages_changed(self):

        # Loop throuhg all the URLs, returning as soon as the first non-match is found
        i = 1
        for url in self.urls:
            self.log_debug("Checking URL_" + str(i) + " to see if changed")
            if url['stored_sha256'] != url['current_sha256']:
                self.log_info("URL_" + str(i) + " changed")
                i = + 1
                return True
            else:
                self.log_debug("URL_" + str(i) + " did not change")
            i += 1

        return False

    # Stores the page content in a new directory based on the timestamp
    def store_new_page_versions(self):
        self.log_info("Storing latest versions in a timestamped directory")

        # Strore the URL content to the s3 bucket
        for url in self.urls:
            url['body_file_handle'].put(Body=url['content'])

    # Sends a simple SNS alert message that a URL has changed
    def send_change_alert(self):
        self.log_info("Sending modification alert")

        # Create the topic if it doesn't exist (this is idempotent)
        topic = self.sns.create_topic(Name=self.alert_sns_channel)
        topic_arn = topic['TopicArn']  # get its Amazon Resource Name

        # Publish a message.
        self.sns.publish(
            Message="One of the watched URLs was modified. Latest version of all files are in the s3 bucket : " + self.data_bucket,
            TopicArn=topic_arn
        )

# This function called by Lambda directly
def lambda_handler(event, context):
    # This is all that's needed, everything is in the constructor
    ff = FileFetcher()

    # Delete the object so it starts fresh on every run
    ff.urls.clear()

    return {
        'statusCode': 200,
        'body': 'success'
    }

# This function called by CLI users
lambda_handler(None, None)
