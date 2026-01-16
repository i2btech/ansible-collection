# logrotate

Rotate logs and upload to S3

# sqlbackup

Backup MariaDB, MySQL and PostgreSQL

## PostgreSQL

From oficial [doc](https://www.postgresql.org/docs/current/app-pgdump.html):

> pg_dump is a utility for exporting a PostgreSQL database. It makes consistent exports even if the database is being used concurrently. pg_dump does not block other users accessing the database (readers or writers). ***Note, however, that except in simple cases, pg_dump is generally not the right choice for taking regular backups of production databases***. See Chapter 25 for further discussion.
