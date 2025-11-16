# AWS

## Backup Restore

This module take the last recovery point of the vault and restore the resource.

The IAM role pass to the module need to have the following managed policies:
- AWSBackupServiceRolePolicyForBackup
- AWSBackupServiceRolePolicyForRestores
- AWSBackupServiceRolePolicyForS3Backup
- AWSBackupServiceRolePolicyForS3Restore
