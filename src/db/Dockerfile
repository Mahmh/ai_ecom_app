FROM postgres:16.4-alpine
COPY schema.sql /docker-entrypoint-initdb.d/
CMD ["postgres", "-D", "/var/lib/postgresql/data"]