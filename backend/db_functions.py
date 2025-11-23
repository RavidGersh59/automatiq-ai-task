import sqlite3
def exist_employee(name, id):
    """"check if an employee exists in the database by name and id"""

    # connect to db
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()


    sql = """
    SELECT * FROM employees
    WHERE EMPLOYEE_ID = ? AND EMPLOYEE_NAME = ?;
    """

    cursor.execute(sql, (id, name))  
    row = cursor.fetchone()                 

    if row: # the employee exists
        return True
    else:
        return False
    


def get_user_division(id):
    """user divison"""
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()

    sql = "SELECT EMPLOYEE_DIVISION FROM employees WHERE EMPLOYEE_ID == ?;"
    cursor.execute(sql, (str(id),))  
    user_division = cursor.fetchone()  
    return user_division[0]




def contains_hebrew(text: str) -> bool: # if the user is a hebrew speaker we will answear in hebrew
    return any('א' <= ch <= 'ת' for ch in text)






def get_column_names():
    # column names
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(employees)")
    columns_info = cursor.fetchall()

    column_names = [col[1] for col in columns_info]
    return column_names



def search(query: str, db_path="employees.db"):
    """
    Executes an SQL query on the given SQLite database and returns the results.
    Returns a tuple: (column_names, rows)
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the provided SQL query
        cursor.execute(query)

        # Fetch all results and column names
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]

        # Return results instead of printing
        return col_names, rows

    except Exception as e:
        return None, []

    finally:
        # Always close the connection
        conn.close()





