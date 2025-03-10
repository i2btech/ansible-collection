i2b.logrotate
=============

Rotate log files using LogRotate, files are uploaded to AWS S3 bucket

Requirements
------------

None

Role Variables
--------------

- `host`: Hostname where the role is executed. This is used to separate logs when multiple hosts are used.
- `service`: Service name which logs are rotated.
- `logs_files`: List of file names to be rotated.
- `logs_directory`: Directory where logs are located.
- `postscript`: Script executed after rotation of logs, is called by LogRotate using sh not bash.
- `logrotate_data`: Directory where old logs are stored. Default `{{ logs_directory }}/rotate/logs`
- `logrotate_keep_for`: Number of old logs files that we keep before delete them. Default `60`
- `s3_bucket`: String, bucket name where files will be uploaded. If this value is not defined the rotated files will not be uploaded to S3 and not be deleted of the host.
- `s3_prefix`: Directory in S3 bucket where object will be upload

Dependencies
------------

- None

Example Playbook
----------------

Rotate logs and upload to S3

```yaml
- hosts: "tag_Role_admin"
  roles:
    - role: i2b.logrotate
      host: "{{ inventory_hostname_short }}"
      service: "nginx"
      postscript: "logrotate/postscript-nginx.j2.sh"
      logs_directory: "/devops/data/nginx/logs"
      logs_files:
        - "access.log"
        - "error.log"
      s3_bucket: "{{ doid }}-logsrotate"
      s3_prefix: "frontend/nginx"

```

License
-------

BSD

Author Information
------------------

IT I2BTech <it@i2btech.com>
