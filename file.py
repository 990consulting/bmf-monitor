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
import json
import boto3
import botocore
import requests
import hashlib

# from botocore.exceptions import ClientError

class Filefetcher:

  # Bucket for data and hash storage
  data_bucket = None

  # URLs to check
  urls = []

  # Alerting sns channel
  alert_sns_channel = None

  # Set this to true by using env var DEBUG
  debug = None

  # Hard coded confg options
  bucket_path_hashes = "hashes"
  bucket_path_data = "files"

  # boto client handles
  s3 = None
  sns = None

  # Default region, override with env AWS_REGION
  aws_region = 'us-east-1'

# Constructor
  def __init__(self):

    # Parses the env vars into the config vars
    self.loadConfig()

    # Setup the s3 handler
    self.s3 = boto3.resource('s3')

    # Setup the sns handler
    self.sns = boto3.client(
        'sns',
        region_name=self.aws_region
    )

    # Fetch past hashes for comparison to present
    self.loadKnownHashesFromS3()

    # Fetch all URLs to check for change
    self.checkUrls()

    # Check if pages have changed or not and handle
    if self.havePagesChanged():
        self.logInfo("Pages have changed - triggering change actions")
        self.sendChangeAlert()
    else:
        self.logInfo("No pages have changed - no further action required")


    self.logInfo("Exiting successfully")

  ########################
  # Logging Methods
  ########################

  # Generic method to handle all log levels
  def logWrite(self,level,msg):
    # Don't print debug out of debug mode
    if level is not 'debug' or self.debug:

        # flush=true means that the log messages are never buffered
        print("[" + self.logTime() + "] [" + level.upper() + "] " + str(msg), flush=True)

  # lturn a string with the timestamp for consistent logging purposes
  def logTime(self):
      return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

  # Function to write an debug log
  # This method used in the main program
  def logDebug(self, msg):
    self.logWrite('debug', msg)

  # Function to write an info log
  # This method used in the main program
  def logInfo(self, msg):
    self.logWrite('info ', msg)

  # Function to write a fatal log and exit w/ code 1
  # This method used in the main program to
  def logFatal(self, msg):
    self.logWrite('fatal', msg)
    exit(1)


  ########################
  # Main Methods
  ########################

  # Loads and verifies the configuration from environment variables
  def loadConfig(self):

    # Check for debug mode
    if "DEBUG" in os.environ and (os.environ['DEBUG'].lower() in ['1', 'true', 'yes', 'on']):
        self.debug = True
        self.logDebug("Debug mode enabled")

    self.logInfo("Loading configuration")

    # Check if DATA_BUCKET is set
    # If not, fail hard. Can not run with a default
    if "DATA_BUCKET" in os.environ:
        self.data_bucket = os.environ['DATA_BUCKET']
        self.logDebug("data_bucket set to '" + self.data_bucket + "' with environment variable 'DATA_BUCKET'")
    else:
        self.logFatal("Environment variable 'DATA_BUCKET' is not set")

    # Check if ALERT_SNS_CHANNEL is set
    # If not, fail to empty. Can still run without an alerting email
    if "ALERT_SNS_CHANNEL" in os.environ:
        self.alert_sns_channel = os.environ['ALERT_SNS_CHANNEL']
        self.logDebug("alert_sns_channel set to '" + self.alert_sns_channel + "' with environment variable 'ALERT_SNS_CHANNEL'")
    else:
        self.logDebug("Environment variable 'ALERT_SNS_CHANNEL' is not set. Defaulting to blank.")


    # Check for aws region override - default set above
    if "AWS_REGION" in os.environ:
        self.aws_region = os.environ['AWS_REGION']

    self.logInfo("Region set to " + self.aws_region)

    # Parse in URLs
    # Read in as many as exist, but fail hard if the first is not found. Can not run with a default
    # Will read in environment variables URL_1, URL_2, URL_3, ..., URL_n into list 'self.urls'
    #
    # Hard fails if at least URL_1 not set

    i = 1
    while True:
        varname = "URL_" + str(i)
        if varname in os.environ:
            self.urls.append({
                "url": os.environ[varname],
                "stored_sha256": '', # to be filled later
                "current_sha256": '', # to be filled later
            })
            self.logDebug("Environment variable '" + varname + "' set to " + os.environ[varname])
        else:
            # Hard fail if on the first loop
            if(i == 1):
                self.logFatal("URL_1 was not found - can not continue without at least one URL")
            # Otherwise, simply exit the loop, since we've parsed all the entries
            else:
                self.logInfo("Parsed " + str(len(self.urls)) + " URLs into the configuration")
                break
        i += 1

    self.logDebug("Confguration successfully loaded")

  # Loads old known hashes from s3 bucket to check for changes
  def loadKnownHashesFromS3(self):

    self.logDebug("Loading previously known hashes from s3")

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
            self.logDebug("File " + hash_filepath + " found in bucket " + self.data_bucket + " - hash : " + url['stored_sha256'])

        except self.s3.meta.client.exceptions.NoSuchKey:
            self.logInfo("File " + hash_filepath + " not found in bucket " + self.data_bucket + " - assuming blank hash and writing blank file")

            # Write blank file for future writing
            url['hash_file_handle'].put(Body=b'')

            # Put blank value in data array to blank
            url['stored_sha256'] = ''

        i += 1

  # Checks all the URLs
  def checkUrls(self):
    self.logDebug("Checking URLs against previously known hashes")

    # Loop through all URLs
    i = 1
    for url in self.urls:

        r = requests.get(url['url'], allow_redirects=True, timeout=10)

        # Only continue handling if it was a 200
        if r.status_code != 200:
            self.logInfo("URL_" + str(i) + " returned HTTP code of " + str(r.status_code) + " - skipping")
            i += 1

            # Write hash blank for change detection, don't clear body so that
            # we still have it in event of a brief client-side outage
            url['hash_file_handle'].put(Body='')
            continue

        # Calculate page hash
        hashContent = str(r.text).encode('utf-8')

        sha256 = hashlib.sha256(hashContent).hexdigest()
        self.logDebug("URL_" + str(i) + " returned HTTP code of " + str(r.status_code))
        self.logInfo("URL_" + str(i) + " sha256 = " + sha256)

        # Store to data array
        url['current_sha256'] = sha256

        # Write hash and content to s3 bucket as well
        url['hash_file_handle'].put(Body=sha256)
        url['body_file_handle'].put(Body=r.text)

        i += 1

  # Compares the past and current page hash to see if any pages have changed
  # returns bool, true means pages have changed, false means pages are the same
  def havePagesChanged(self):

    # Loop throuhg all the URLs, returning as soon as the first non-match is found
    i = 1
    for url in self.urls:
        self.logDebug("Checking URL_" + str(i) + " to see if changed")
        if url['stored_sha256'] != url['current_sha256']:
            self.logInfo("URL_" + str(i) + " changed")
            i =+ 1
            return True
        else:
            self.logDebug("URL_" + str(i) + " did not change")
        i += 1

    return False

  # Sends a simple SNS alert message that a URL has changed
  def sendChangeAlert(self):
      self.logInfo("Sending modification alert")

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
    ff = Filefetcher()

    # Delete the object so it starts fresh on every run
    ff.urls = []
    del ff

    return {
        'statusCode': 200,
        'body': 'success'
    }

# This function called by CLI users
lambda_handler(None,None)
