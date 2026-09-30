FROM mysql:8.0
ENV MYSQL_DATABASE=ccps
COPY ccps_dump.sql /docker-entrypoint-initdb.d/01-dump.sql
