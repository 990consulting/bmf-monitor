# TODO

Program is more-or-less done.

Left to develop:

 * Fill in SNS sending logic with boto in function sendChangeAlert()
 * Upload to lambda and ensure it still works (early versions were tested there so it shouldn't be far off)
 * Adjust lambda config


Left to do other-than-dev:
 * Write restricted IAM policy to only write to singular bucket
 * Apply restricted IAM policy to lambda function
 * Cleanup / rewrite docs
 * Document / automate (aws CLI) lambda configuration 
