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
from email.utils import parseaddr
import boto3

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
  bucket_path_hashes = "hashes/sha256"
  bucket_path_data = "data"

  # s3 handle
  s3 = None

  # Constructor
  def __init__(self):

    # Parses the env vars into the config vars
    self.loadConfig()

    # Setup the s3 handler
    self.s3 = boto3.resource('s3')

    self.loadKnownHashes()
    self.checkUrls()

    self.logInfo("Exiting successfully")

  ########################
  # Logging Methods
  ########################

  # Generic method to handle all log levels
  def logWrite(self,level,msg):
    # Don't print debug out of debug mode
    if level is not 'debug' or self.debug:
        print("[" + self.logTime() + "] [" + level.upper() + "] " + str(msg))

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
        data_bucket = os.environ['DATA_BUCKET']
        self.logDebug("data_bucket set to '" + data_bucket + "' with environment variable 'DATA_BUCKET'")
    else:
        self.logFatal("Environment variable 'DATA_BUCKET' is not set")

    # Check if ALERT_SNS_CHANNEL is set
    # If not, fail to empty. Can still run without an alerting email
    if "ALERT_SNS_CHANNEL" in os.environ:
        self.alert_sns_channel = os.environ['ALERT_SNS_CHANNEL']
        self.logDebug("alert_sns_channel set to '" + self.alert_sns_channel + "' with environment variable 'ALERT_SNS_CHANNEL'")
    else:
        self.logDebug("Environment variable 'ALERT_SNS_CHANNEL' is not set. Defaulting to blank.")

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

    self.logDebug(self.urls)
    self.logDebug("Confguration successfully loaded")


  # Checks all the URLs
  def loadKnownHashes(self):
    """
    s3 = boto3.resource('s3')

    for bucket in s3.buckets.all():
        print(bucket.name)
    """

    # Loop through all URLs
    url_count = 1
    for url in self.urls:

        filepath = self.bucket_path_hashes + '/url_' + str(url_count)

        obj = self.s3.Object(self.data_bucket, filepath)
        obj.get()['Body'].read().decode('utf-8')

        url_count += 1

    self.logDebug("Loading previously known hashes from s3")

  # Checks all the URLs
  def checkUrls(self):
     self.logDebug("Checking URLs against previously known hashes")



# This function called by Lambda directly
def lambda_handler(event, context):

    # This is all that's needed, everything is in the constructor
    ff = Filefetcher()

    # Delete the object so it starts fresh on every run
    ff.urls = []
    del ff

    return {
        'statusCode': 200,
        'body': ''
    }

# This function called by CLI users
lambda_handler(None,None)
