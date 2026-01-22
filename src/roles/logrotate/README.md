i2btech.ops.logrotate
====================

Rotate log files using LogRotate, files are uploaded to AWS S3 bucket.

When the files are uploaded to S3 we use the variables `service` and `hosts` as a prefix in S3.

Requirements
------------

None

Role Variables
--------------

- `host`: Hostname where the role is executed.
- `service`: Service name which logs are rotated.
- `logs_directories_list`: Directory where logs are located.
- `logrotate_keep_for`: Number of old logs files that we keep before delete them. Default `60`
- `s3_bucket_upload`: String, bucket name where files will be uploaded. If this value is not defined the rotated files will not be uploaded to S3 and not be deleted of the host.
- `logrotate_delete_files_after_rotate`: String, if TRUE delete logs files after rotate. Default `FALSE`

Dependencies
------------

- None

Example Playbook
----------------

Rotate logs and upload to S3

```yaml
- hosts: "tag_Role_admin"
  roles:
    - role: i2btech.ops.logrotate
      host: "web-server"
      service: "nginx"
      logs_directories_list:
        - "/devops/data/nginx/logs"
      s3_bucket_upload: "{{ doid }}-logsrotate"
      logrotate_delete_files_after_rotate: "TRUE"
```

License
-------

BSD

Author Information
------------------

IT I2BTech <it@i2btech.com>
