import psycopg2


class DbConnectionFactory:

    @staticmethod
    def get_new_connection(conn_url):
        try:
            conn = psycopg2.connect(conn_url)
            return conn
        except:
            print("Unable to connect to database")
