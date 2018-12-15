# docker build -t app . &&

docker run \
 -v "${PWD}:/app" \
 -v "${HOME}/.aws/credentials:/root/.aws/credentials" \
 -e "ALERT_SNS_CHANNEL=jdoe@example.com" \
 -e "DEBUG=0" \
 -e "DATA_BUCKET=bmf-bucket" \
 -e "URL_1=https://benyanke.com/tmp/file1" \
 -e "URL_2=https://benyanke.com/tmp/file2" \
 -e "URL_3=https://benyanke.com/tmp/file3" \
 -e "URL_4=https://benyanke.com/tmp/file4" \
 -e "URL_5=https://benyanke.com/tmp/file5" \
 app

