DB = "postgres"                     #: type of database: postgres, oracle, default postgres
USER_NAME = "luna"                  #: login to database
PASSWORD_DB = "luna"                #: password to database
DB_HOST = "127.0.0.1"               #: ip-address of database
DB_PORT = 5432                      #: database listener port, 5432 - default port of postgres, 1521 - default port of oracle
DB_NAME = "luna_faces"              #: name of database for postgres, sid name for oracle

if DB == "postgres":
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(USER_NAME, PASSWORD_DB, DB_HOST,DB_PORT,
                                                                   DB_NAME)  #: postgresql address
elif DB == "oracle":
    SQLALCHEMY_DATABASE_URI = 'oracle+cx_oracle://{}:{}@{}:{}/{}'.format(USER_NAME, PASSWORD_DB, DB_HOST, DB_PORT,
                                                                         DB_NAME)  #: oracle address
