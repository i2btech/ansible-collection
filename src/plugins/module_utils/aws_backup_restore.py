"""
Util class for aws_backup_restore
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from ansible_collections.i2btech.ops.plugins.module_utils.file_logger import FileLogger
import uuid
import time


#
# class: AWSBackupRestoreHelper
#

class AWSBackupRestoreHelper:
    """
    Class AWSBackupRestoreHelper
    """

    def __init__(self, module):
        self.module = module
        self.current_date=str(datetime.today().strftime('%Y-%m-%d')) + " 00:00:00"

    def get_efs_info(self):
        """
        Get information of EFS
        """

        EFS_EXIST=False
        client_efs = boto3.client('efs', region_name=self.module.params['aws_region'])

        # Check if Filesystem exists...
        response = client_efs.describe_file_systems()
        for FS in response["FileSystems"]:
            for tags in FS["Tags"]:
                if tags["Key"] == 'Name':
                    if tags["Value"] == self.module.params['resource_name']:
                        EFS_EXIST=True

        return EFS_EXIST


    def get_s3_info(self):
        """
        Get information of S3
        """

        logger = FileLogger()
        logger.info("Check if Bucket  exists...")

        BUCKET_EXISTS=False
        client_s3 = boto3.client('s3', region_name=self.module.params['aws_region'])

        try:
            client_s3.head_bucket(Bucket=self.module.params['resource_name'])
            BUCKET_EXISTS=True
            logger.info("Bucket  exists...")
        except ClientError as e:
            BUCKET_EXISTS=False
            logger.info("Bucket  don't exists...")

        logger.close()
        return BUCKET_EXISTS


    def get_kms_key_id_by_alias(self, alias_name):
        """
        Retrieves the KMS Key ID for a given alias name.

        Args:
            alias_name (str): The alias name (e.g., "alias/my-key-alias").

        Returns:
            str: The KMS Key ID if found, None otherwise.
        """
        kms_client = boto3.client('kms', region_name=self.module.params['aws_region'])
        try:
            response = kms_client.describe_key(KeyId=alias_name)
            key_id = response['KeyMetadata']['KeyId']
            return key_id
        except kms_client.exceptions.NotFoundException:
            print(f"Alias '{alias_name}' not found.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


    def efs_restore(self):

        result = {
            "changed": False,
            "failed": False,
            "message": []
        }

        logger = FileLogger()
        client_efs = boto3.client('efs', region_name=self.module.params['aws_region'])

        logger.info("Filesystem don't exists, restoring...")
        client_backup = boto3.client('backup', region_name=self.module.params['aws_region'])

        # Get recovery point EFS...
        response_get_point = client_backup.list_recovery_points_by_backup_vault(
            BackupVaultName=self.module.params['vault_name'],
            MaxResults=1,
            ByResourceType='EFS',
            ByCreatedAfter=self.current_date
        )

        # Create filesystem from backup...
        response_restore_start = client_backup.start_restore_job(
            RecoveryPointArn=response_get_point["RecoveryPoints"][0]["RecoveryPointArn"],
            Metadata={
                "file-system-id": "dummy",
                "Encrypted": "true",
                "KmsKeyId": self.get_kms_key_id_by_alias("alias/aws/elasticfilesystem"),
                "PerformanceMode": "generalPurpose",
                "CreationToken": str(uuid.uuid4()),
                "newFileSystem": "true"            
            },
            IamRoleArn=self.module.params['iam_role_restore'],
            IdempotencyToken=str(uuid.uuid4()),
            ResourceType='EFS',
            CopySourceTagsToRestoredResource=False
        )

        # Waiting for filesystem...
        force_exit=0
        while True:
            response_restore_status = client_backup.describe_restore_job(
                RestoreJobId=response_restore_start["RestoreJobId"]
            )
            time.sleep(10)
            force_exit += 1
            status = response_restore_status["Status"] # values: 'PENDING'|'RUNNING'|'COMPLETED'|'ABORTED'|'FAILED'
            logger.info("status: " + status + ", " + response_restore_status["PercentDone"])

            if status == "COMPLETED": 
                result['changed'] = True
                result["message"].append("Filesystem created")

                logger.info("Tag new filesystem...")
                response_tag = client_efs.tag_resource(
                    ResourceId=response_restore_status["CreatedResourceArn"].split(":")[5].split("/")[1],
                    Tags=[
                        {
                            'Key': 'Name',
                            'Value': self.module.params['resource_name']
                        },
                    ]
                )
                result["message"].append("Filesystem tagged")
                break

            if status == "ABORTED" or status == "FAILED": 
                result['failed'] = True
                result["message"].append("Creation of filesystem was oborted or failed")
                result["message"].append(response_restore_status)
                break

            if force_exit > 60:
                result['failed'] = True
                result["message"].append("The process took to long, force exit...")
                result["message"].append("Percent done: " + response_restore_status["PercentDone"])
                break

        logger.close()
        return result

    def s3_restore(self):

        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        logger = FileLogger()
        client_backup = boto3.client('backup', region_name=self.module.params['aws_region'])

        logger.info("Get recovery point EFS...")
        response_get_point = client_backup.list_recovery_points_by_backup_vault(
            BackupVaultName=self.module.params['vault_name'],
            MaxResults=1,
            ByResourceType='S3',
            ByCreatedAfter=self.current_date
        )
        logger.info(response_get_point["RecoveryPoints"][0]["RecoveryPointArn"])
        logger.info("Create bucket from backup...")

        response_restore_start = client_backup.start_restore_job(
            RecoveryPointArn=response_get_point["RecoveryPoints"][0]["RecoveryPointArn"],
            Metadata={
                "DestinationBucketName": self.module.params['resource_name'],
                "EncryptionType": "SSE-S3"
            },
            IamRoleArn=self.module.params['iam_role_restore'],
            IdempotencyToken=str(uuid.uuid4()),
            ResourceType='S3',
            CopySourceTagsToRestoredResource=False
        )

        logger.info("Waiting for restoration job to finish...")
        force_exit=0
        while True:
            response_restore_status = client_backup.describe_restore_job(
                RestoreJobId=response_restore_start["RestoreJobId"]
            )
            time.sleep(10)
            force_exit += 1
            status = response_restore_status["Status"] # values: 'PENDING'|'RUNNING'|'COMPLETED'|'ABORTED'|'FAILED'
            logger.info("status: " + status + ", " + response_restore_status["PercentDone"])

            if status == "COMPLETED": 
                result['changed'] = True
                result["message"].append("Bucket created")
                break

            if status == "ABORTED" or status == "FAILED": 
                result['failed'] = True
                result["message"].append("Creation of bucket was oborted or failed")
                result["message"].append(response_restore_status)
                break

            if force_exit > 60:
                result['failed'] = True
                result["message"].append("The process took to long, force exit...")
                result["message"].append("Percent done: " + response_restore_status["PercentDone"])
                break

        logger.info(result["message"])
        logger.close()
        return result
