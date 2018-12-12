export AWS_KEY_ID='key1'
export AWS_SECRET_KEY='key2'

export URL_1='https://www.irs.gov/pub/irs-soi/eo1.csv'
export URL_2='https://www.irs.gov/pub/irs-soi/eo2.csv'
export URL_3='https://www.irs.gov/pub/irs-soi/eo3.csv'
export URL_4='https://www.irs.gov/pub/irs-soi/eo4.csv'
export DATA_BUCKET='s3here'

go fmt && go build && ./bmf-monitor

