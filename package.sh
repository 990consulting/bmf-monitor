#!/bin/bash

# Run this to create a zip file which can be uploaded to s3

rm lambda-package.zip 2> /dev/null
GOOS=linux go build -o bmf-monitor main.go
zip lambda-package.zip ./bmf-monitor
