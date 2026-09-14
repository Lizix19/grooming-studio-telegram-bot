import pyodbc
from config import CONNECTION_STRING
from datetime import datetime, timedelta, time


def get_connection():
    return pyodbc.connect(CONNECTION_STRING)


def get_vidy():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_vid, nazvanie FROM vid")
        return cursor.fetchall()


def get_porody_by_vid(vid_name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id_porody, p.nazvanie
            FROM poroda_pitomtsev p
            JOIN vid v ON p.id_vid = v.id_vid
            WHERE v.nazvanie = ?
        """, (vid_name,))
        return cursor.fetchall()


def get_uslugi():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_uslugi, nazvanie, stoimost FROM uslugi")
        return cursor.fetchall()


def get_dop_materialy():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id_dop_material AS id_dop,
                naimenovanie AS nazvanie,
                tsena AS stoimost
            FROM dop_materialy
        """)
        return cursor.fetchall()


def get_occupied_datetimes():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data_i_vremya_zapisi FROM zapis_na_uslugu")
        return [row[0] for row in cursor.fetchall()]


def get_occupied_dates():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT CONVERT(date, data_i_vremya_zapisi) FROM zapis_na_uslugu")
        return [row[0].strftime("%Y-%m-%d") for row in cursor.fetchall()]


def generate_free_dates():
    today = datetime.today().date()
    free = []
    for i in range(30):  # ближайшие 30 дней
        date = today + timedelta(days=i)
        if date.weekday() < 6:  # кроме воскресений
            free.append(date.strftime("%Y-%m-%d"))
    return free


def get_free_times_for_date(selected_date_str):
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    occupied = get_occupied_datetimes()
    possible_times = [time(hour=h) for h in range(10, 19)]
    free_times = []
    for t in possible_times:
        dt = datetime.combine(selected_date, t)
        if not any(occ_dt.date() == dt.date() and occ_dt.hour == dt.hour and occ_dt.minute == dt.minute for occ_dt in occupied):
            free_times.append(t.strftime("%H:%M"))
    return free_times


def save_full_zapis(data):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id_vid FROM vid WHERE nazvanie = ?", data['vid'])
        row = cursor.fetchone()
        if row:
            id_vid = row[0]
        else:
            cursor.execute("INSERT INTO vid (nazvanie) OUTPUT INSERTED.id_vid VALUES (?)", (data['vid'],))
            id_vid = cursor.fetchone()[0]

        cursor.execute("""
            SELECT id_porody FROM poroda_pitomtsev
            WHERE nazvanie = ? AND id_vid = ?
        """, (data['poroda'], id_vid))
        row = cursor.fetchone()
        if row:
            id_porody = row[0]
        else:
            cursor.execute("""
                INSERT INTO poroda_pitomtsev (nazvanie, id_vid)
                OUTPUT INSERTED.id_porody
                VALUES (?, ?)
            """, (data['poroda'], id_vid))
            id_porody = cursor.fetchone()[0]

        cursor.execute("""
            SELECT id_klienta FROM klienty
            WHERE imya = ? AND familiya = ? AND telefon = ?
        """, (data['client_imya'], data['client_familiya'], data['client_phone']))
        row = cursor.fetchone()
        if row:
            id_klienta = row[0]
        else:
            cursor.execute("""
                INSERT INTO klienty (imya, familiya, telefon, email, adres)
                OUTPUT INSERTED.id_klienta
                VALUES (?, ?, ?, ?, ?)
            """, (
                data['client_imya'], data['client_familiya'],
                data['client_phone'], data.get('client_email', None), data.get('client_address', None)
            ))
            id_klienta = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO pitomtsy (imya, data_rozhdeniya, id_poroda, id_klienta)
            OUTPUT INSERTED.id_pitomtsa
            VALUES (?, ?, ?, ?)
        """, (
            data['name'], data['birthday'], id_porody, id_klienta
        ))
        id_pitomtsa = cursor.fetchone()[0]

        time_str = data['time']
        if len(time_str.split(':')) == 2:
            time_str += ":00"
        data_i_vremya_str = f"{data['date']} {time_str}"
        data_i_vremya_dt = datetime.strptime(data_i_vremya_str, "%Y-%m-%d %H:%M:%S")

        id_sotrudnika = 1
        cursor.execute("""
            INSERT INTO zapis_na_uslugu (id_pitomtsa, data_i_vremya_zapisi, id_status, id_sotrudnika)
            OUTPUT INSERTED.id_zapisi
            VALUES (?, ?, ?, ?)
        """, (id_pitomtsa, data_i_vremya_dt, 1, id_sotrudnika))
        id_zapisi = cursor.fetchone()[0]

        total = 0
        usluga_names = []
        for id_uslugi in data['uslugi']:
            cursor.execute("INSERT INTO uslugi_v_zapisi (id_zapisi, id_uslugi) VALUES (?, ?)", (id_zapisi, id_uslugi))
            cursor.execute("SELECT nazvanie, stoimost FROM uslugi WHERE id_uslugi = ?", (id_uslugi,))
            row = cursor.fetchone()
            if row:
                usluga_names.append(row[0])
                total += row[1]

        dop_names = []
        if 'dop_materialy' in data:
            for id_dop_material in data['dop_materialy']:
                cursor.execute("INSERT INTO dop_v_zapisi (id_zapis, id_dop_material) VALUES (?, ?)", (id_zapisi, id_dop_material))
                cursor.execute("SELECT naimenovanie, tsena FROM dop_materialy WHERE id_dop_material = ?", (id_dop_material,))
                row = cursor.fetchone()
                if row:
                    dop_names.append(row[0])
                    total += row[1]

        cursor.execute("UPDATE zapis_na_uslugu SET k_oplate = ? WHERE id_zapisi = ?", (total, id_zapisi))
        conn.commit()

        client = f"{data['client_imya']} {data['client_familiya']}"
        pet = data['name']
        uslugi_str = ', '.join(usluga_names)
        dop_str = ', также ' + ', '.join(dop_names) if dop_names else ''
        date_time_str = f"{data['date']} {data['time']}"
        total_str = f"{total} ₽"

        return f"{client}, мы записали вашего {pet} на *{uslugi_str}*{dop_str} на {date_time_str}. К оплате будет {total_str}."



# АДМИНСКИЙ РАЗДЕЛ

ALLOWED_TABLES = {
    "vid", "poroda_pitomtsev", "klienty", "pitomtsy", "status",
    "sotrudniki", "uslugi", "zapis_na_uslugu", "dop_materialy",
    "uslugi_v_zapisi", "dop_v_zapisi", "otzyvy",
}


def _check_table_allowed(table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Таблица '{table_name}' не входит в список разрешённых")


def get_table_names():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME NOT LIKE 'sysdiagrams'
        """)
        actual_tables = {row[0] for row in cursor.fetchall()}
    return sorted(actual_tables & ALLOWED_TABLES)


def get_table_columns(table_name):
    _check_table_allowed(table_name)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, (table_name,))
        return [row[0] for row in cursor.fetchall()]


def get_table_data(table_name):
    _check_table_allowed(table_name)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return columns, [dict(zip(columns, row)) for row in rows]


def add_data_to_table(table_name, data: dict):
    _check_table_allowed(table_name)
    allowed_columns = set(get_table_columns(table_name))
    unknown = set(data.keys()) - allowed_columns
    if unknown:
        raise ValueError(f"Неизвестные столбцы для таблицы {table_name}: {unknown}")
    with get_connection() as conn:
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' for _ in data)
        values = tuple(data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()


def delete_data_from_table(table_name, row_id):
    _check_table_allowed(table_name)
    id_column = get_table_columns(table_name)[0]  # первый столбец = первичный ключ
    with get_connection() as conn:
        cursor = conn.cursor()
        query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
        cursor.execute(query, (row_id,))
        conn.commit()


def update_table_data(table_name, row_id, updates: dict):
    _check_table_allowed(table_name)
    allowed_columns = set(get_table_columns(table_name))
    unknown = set(updates.keys()) - allowed_columns
    if unknown:
        raise ValueError(f"Неизвестные столбцы для таблицы {table_name}: {unknown}")
    id_column = get_table_columns(table_name)[0]
    with get_connection() as conn:
        cursor = conn.cursor()
        set_clause = ', '.join([f"{key} = ?" for key in updates])
        values = list(updates.values()) + [row_id]
        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
        cursor.execute(query, values)
        conn.commit()
