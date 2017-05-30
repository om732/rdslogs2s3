rdslogs2es
===

Save RDS Logs file to S3.

## Require
- python3
- boto3

## RDS Parametar
|key|value|
|:--|:--|
|log_output|FILE|

http://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Concepts.MySQL.html

## IAM Role

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::[BucketName]/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::[BucketName]"
            ]
        },
        {

            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBLogFiles",
                "rds:DownloadDBLogFilePortion"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

## Environment

|Key|Value|
|:---|:---|
|RDS_INSTANCE|RDS instance Name|
|LOG_NAME|RDS log name|
|S3_BUCKET|Save s3 bucket name|
|S3_KEY_PREFIX|Object key prefix|
|REGION|aws region for RDS/S3|
|TZ|timezone|
