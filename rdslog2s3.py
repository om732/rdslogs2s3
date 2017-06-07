#!/bin/env python
# coding=utf-8
#
# environment
# ```
# export RDS_INSTANCE=<rds instance name>
# export LOG_NAME=<rds log name>
# export S3_BUCKET=<save log bucker name>
# export S3_KEY_PREFIX=<save key prefix>
# export REGION=<aws region>
# export TZ=<timezone>
# ```
#
import sys
import os
import gzip
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

RDS_INSTANCE = os.environ['RDS_INSTANCE']
LOG_NAME = os.environ['LOG_NAME']
S3_BUCKET = os.environ['S3_BUCKET']
S3_KEY_PREFIX = os.environ['S3_KEY_PREFIX']
REGION = os.environ['REGION']

now = datetime.now().strftime('%Y%m%d%H%M%S')

def lambda_handler(event, context):
    read_log_line_num = 2000
    rds = boto3.client('rds', region_name=REGION)
    s3 = boto3.client('s3', region_name=REGION)

    db_logs = rds.describe_db_log_files(DBInstanceIdentifier=RDS_INSTANCE, FilenameContains=LOG_NAME)

    for db_log in db_logs['DescribeDBLogFiles']:
        log_file_name = db_log['LogFileName']
        markerfile_name = '{0}{1}/{2}/markerfile'.format(S3_KEY_PREFIX, RDS_INSTANCE, log_file_name)
        try:
            markerfile_obj = s3.get_object(Bucket=S3_BUCKET, Key=markerfile_name)
            marker = str(object=markerfile_obj['Body'].read(), encoding='utf-8')
            print("markerfile found. read form '{0}', {1}".format(marker, log_file_name))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print("markerfile not found. run full scan: {}".format(log_file_name))
                marker = '0'
            else:
                print("Unexpected error: {}".format(e))
                return "Failed"

        local_log_name = '/tmp/{0}-{1}.log.gz'.format(log_file_name.replace('/', '-'), now)
        with gzip.open(local_log_name, 'ab') as f:
            exists_data = True
            loop = 0

            while exists_data:
                log = rds.download_db_log_file_portion(DBInstanceIdentifier=RDS_INSTANCE, LogFileName=log_file_name, NumberOfLines=read_log_line_num, Marker=marker)

                if log['LogFileData']:
                    if "[Your log message was truncated]" in log['LogFileData']:
                        read_log_line_num -= int(read_log_line_num * 0.1)
                        print("found `truncated` message. retry line num, {}".format(read_log_line_num))
                        continue
                    f.write(log['LogFileData'].encode('utf-8'))
                    marker = log['Marker']
                    loop += 1
                else:
                    exists_data = False

        if loop != 0:
            try:
                put_log_name = '{0}{1}/{2}/{3}.log.gz'.format(S3_KEY_PREFIX, RDS_INSTANCE, log_file_name, now)
                s3.upload_file(local_log_name, S3_BUCKET, put_log_name)
                print('put s3://{0}/{1}'.format(S3_BUCKET, put_log_name))
                os.remove(local_log_name)

                s3.put_object(Bucket=S3_BUCKET, Key=markerfile_name, Body=marker)
                print('put s3://{0}/{1}, now position {2}'.format(S3_BUCKET, markerfile_name, marker))
            except ClientError as e:
                print("Unexpected error: {}".format(e))
                return "Failed"

    return "Success"

if __name__ == "__main__":
    lambda_handler(None, None)
