from util import logConfig, logger, lumos

def init_db(conn, table="master"):
    cursor = conn.cursor()

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table} (
        vid TEXT PRIMARY KEY NOT NULL UNIQUE,
        symbol TEXT NOT NULL,
        nickname TEXT NOT NULL,
        md5 TEXT NOT NULL
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()

    logger.debug("Table created successfully.")


def insert_db(conn, table, data_dict):
    cursor = conn.cursor()
    columns = ", ".join(data_dict.keys())
    placeholders = ", ".join(["?"] * len(data_dict))
    insert_sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.execute(insert_sql, tuple(data_dict.values()))
    conn.commit()
    logger.debug(f"Data inserted with ID: {data_dict['vid']}")


def fetch_db_by_vid(conn, table, vid):
    cursor = conn.cursor()
    fetch_sql = f"SELECT * FROM {table} WHERE vid=?"
    cursor.execute(fetch_sql, (vid,))
    result = cursor.fetchone()
    if result:
        return tuple_to_dict(cursor, result)
    else:
        return None

def fetch_db_all(conn, table="master"):
    cursor = conn.cursor()
    fetch_all_sql = f"SELECT * FROM {table}"
    cursor.execute(fetch_all_sql)
    results = cursor.fetchall()
    if results:
        return [tuple_to_dict(cursor, row) for row in results]
    else:
        return []

def update_db_by_vid(conn, table, vid, new_values):
    cursor = conn.cursor()
    update_sql = (
        "UPDATE {} SET ".format(table)
        + ", ".join(["{}=?".format(k) for k in new_values])
        + " WHERE vid=?"
    )
    values = list(new_values.values()) + [vid]
    cursor.execute(update_sql, values)
    conn.commit()
    logger.debug(f"Data updated with ID: {vid}")


def delete_db_by_vid(conn, table, vid):
    cursor = conn.cursor()
    delete_sql = f"DELETE FROM {table} WHERE id=?"
    cursor.execute(delete_sql, (vid,))
    conn.commit()
    logger.debug(f"Data deleted with ID: {vid}")


def tuple_to_dict(cursor, row):
    return {column[0]: row[idx] for idx, column in enumerate(cursor.description)}

