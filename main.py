import psycopg2
from database.db_utilities import *#create_table, delete_table, table_list, DB_NAME, DB_USER, DB_HOST, DB_PORT

def main():
    """Main function to initialize database and create tables."""
    try:
        connection = psycopg2.connect(database=DB_NAME, user=DB_USER, host=DB_HOST, port=DB_PORT)
        # Delete All for troubleshooting.
        # for table in table_list:
        #     delete_table(connection, [*table][0])
        
        # Create All
        for table in table_list:
            create_table(connection, table)

            
        connection.close()

    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
    
if __name__ == '__main__':
    main()