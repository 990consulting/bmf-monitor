docker build -t app . &&

docker run \
 -v "${PWD}:/app" \
 -e "DEBUG=1" \
 -e "ALERT_SNS_CHANNEL=jdoe@example.com" \
 -e "DATA_BUCKET=1" \
 -e "URL_1=http://example.com/file1.csv" \
 -e "URL_2=http://example.com/file2.csv" \
 -e "URL_3=http://example.com/file3.csv" \
 app

