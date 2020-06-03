ADMIN_DB_TYPE = "postgres"         #: Admin database type: postgres, oracle, default postgres
ADMIN_DB_USER_NAME = "faceis"      #: Admin database login
ADMIN_DB_PASSWORD = "faceis"       #: Admin database password
ADMIN_DB_HOST = "127.0.0.1"        #: Admin database ip-address
ADMIN_DB_PORT = 5432               #: Admin database listener port, 5432 - default port of postgres, 1521 - default port of oracle
ADMIN_DB_NAME = "admin_faceis_db"  #: Admin database name for postgres, sid for oracle, where necessary schemes are created

if ADMIN_DB_TYPE == "postgres":
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(ADMIN_DB_USER_NAME, ADMIN_DB_PASSWORD, ADMIN_DB_HOST,
                                                                   ADMIN_DB_PORT, ADMIN_DB_NAME)  #: postgresql address
elif ADMIN_DB_TYPE == "oracle":
    SQLALCHEMY_DATABASE_URI = 'oracle+cx_oracle://{}:{}@{}:{}/{}'.format(ADMIN_DB_USER_NAME, ADMIN_DB_PASSWORD,
                                                        ADMIN_DB_HOST, ADMIN_DB_PORT, ADMIN_DB_NAME)  #: oracle address
