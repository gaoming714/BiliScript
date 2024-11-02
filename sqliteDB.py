from util import logConfig, logger, lumos

# logConfig("logs/download.log", rotation="10 MB", level="DEBUG", lite=True)


def init_db(conn, table="master"):
    cursor = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS {} (
        vid TEXT PRIMARY KEY NOT NULL UNIQUE,
        symbol TEXT NOT NULL,
        nickname TEXT NOT NULL,
        md5 TEXT NOT NULL
    );
    """.format(
        table
    )
    cursor.execute(create_table_sql)
    conn.commit()

    logger.debug("Table created successfully.")


def insert_db(conn, data_dict, table="master"):
    cursor = conn.cursor()
    columns = ", ".join(data_dict.keys())
    placeholders = ", ".join(["?"] * len(data_dict))
    insert_sql = "INSERT INTO {} ({}) VALUES ({})".format(table, columns, placeholders)
    cursor.execute(insert_sql, tuple(data_dict.values()))
    conn.commit()
    logger.debug(f"Data inserted with ID: {data_dict['vid']}")


def fetch_db_by_vid(conn, vid, table="master"):
    cursor = conn.cursor()
    fetch_sql = "SELECT * FROM {} WHERE vid=?".format(table)
    cursor.execute(fetch_sql, (vid,))
    result = cursor.fetchone()
    if result:
        return tuple_to_dict(cursor, result)
    else:
        return None

def fetch_db_all(conn, table="master"):
    cursor = conn.cursor()
    fetch_all_sql = "SELECT * FROM {}".format(table)
    cursor.execute(fetch_all_sql)
    results = cursor.fetchall()
    if results:
        return [tuple_to_dict(cursor, row) for row in results]
    else:
        return []

def update_db_by_vid(conn, vid, new_values, table="master"):
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


def delete_db_by_vid(conn, vid, table="master"):
    cursor = conn.cursor()
    delete_sql = "DELETE FROM {} WHERE id=?".format(table)
    cursor.execute(delete_sql, (vid,))
    conn.commit()
    logger.debug(f"Data deleted with ID: {vid}")


def tuple_to_dict(cursor, row):
    return {column[0]: row[idx] for idx, column in enumerate(cursor.description)}

def init_mq(conn, table="queue"):
    cursor = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS {} (
        vid TEXT PRIMARY KEY NOT NULL UNIQUE,
        status TEXT,
        symbol TEXT,
        nickname TEXT,
        md5 TEXT
    );
    """.format(
        table
    )
    cursor.execute(create_table_sql)
    conn.commit()

    logger.debug("Table created successfully.")


def insert_mq(conn, data_dict, table="queue"):
    cursor = conn.cursor()
    columns = ", ".join(data_dict.keys())
    placeholders = ", ".join(["?"] * len(data_dict))
    insert_sql = "INSERT INTO {} ({}) VALUES ({})".format(table, columns, placeholders)
    cursor.execute(insert_sql, tuple(data_dict.values()))
    conn.commit()
    logger.debug(f"Data inserted with ID: {data_dict['vid']}")


def fetch_mq_by_vid(conn, vid, table="queue"):
    cursor = conn.cursor()
    fetch_sql = "SELECT * FROM {} WHERE vid=?".format(table)
    cursor.execute(fetch_sql, (vid,))
    result = cursor.fetchone()
    if result:
        return tuple_to_dict(cursor, result)
    else:
        return None

def fetch_mq_all(conn, table="queue"):
    cursor = conn.cursor()
    fetch_all_sql = "SELECT * FROM {}".format(table)
    cursor.execute(fetch_all_sql)
    results = cursor.fetchall()
    if results:
        return [tuple_to_dict(cursor, row) for row in results]
    else:
        return []

def fetch_mq(conn, table="queue"):
    cursor = conn.cursor()
    fetch_vids_sql = "SELECT vid FROM {}".format(table)
    cursor.execute(fetch_vids_sql)
    vids = [row[0] for row in cursor.fetchall()]
    return vids

def update_mq_by_vid(conn, vid, new_values, table="queue"):
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


def delete_mq_by_vid(conn, vid, table="queue"):
    cursor = conn.cursor()
    delete_sql = "DELETE FROM {} WHERE vid=?".format(table)
    cursor.execute(delete_sql, (vid,))
    conn.commit()
    logger.debug(f"Data deleted with ID: {vid}")
