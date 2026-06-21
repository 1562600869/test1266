import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'camp.db')

AGE_GROUPS = ['U10', 'U12', 'U14', 'U16', '成人']
POSITIONS = ['控卫', '得分后卫', '小前锋', '大前锋', '中锋']
CAMP_STATUSES = ['报名中', '进行中', '已结束']


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_conn()
    try:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                age_group TEXT NOT NULL CHECK(age_group IN ('U10','U12','U14','U16','成人')),
                position TEXT NOT NULL CHECK(position IN ('控卫','得分后卫','小前锋','大前锋','中锋')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS camps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                fee INTEGER NOT NULL,
                max_capacity INTEGER NOT NULL CHECK(max_capacity > 0),
                status TEXT NOT NULL DEFAULT '报名中' CHECK(status IN ('报名中','进行中','已结束')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                camp_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
                FOREIGN KEY(camp_id) REFERENCES camps(id) ON DELETE CASCADE,
                UNIQUE(player_id, camp_id)
            );

            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                camp_id INTEGER NOT NULL,
                checkin_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
                FOREIGN KEY(camp_id) REFERENCES camps(id) ON DELETE CASCADE,
                UNIQUE(player_id, camp_id, checkin_date)
            );
        ''')
        conn.commit()
    finally:
        conn.close()


def list_players():
    conn = get_conn()
    try:
        rows = conn.execute('SELECT * FROM players ORDER BY id DESC').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def add_player(nickname, phone, age_group, position):
    if age_group not in AGE_GROUPS:
        raise ValueError(f'无效的年龄组，必须是: {", ".join(AGE_GROUPS)}')
    if position not in POSITIONS:
        raise ValueError(f'无效的位置，必须是: {", ".join(POSITIONS)}')
    conn = get_conn()
    try:
        cur = conn.execute(
            'INSERT INTO players (nickname, phone, age_group, position) VALUES (?, ?, ?, ?)',
            (nickname, phone, age_group, position)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_player(player_id, nickname, phone, age_group, position):
    if age_group not in AGE_GROUPS:
        raise ValueError(f'无效的年龄组，必须是: {", ".join(AGE_GROUPS)}')
    if position not in POSITIONS:
        raise ValueError(f'无效的位置，必须是: {", ".join(POSITIONS)}')
    conn = get_conn()
    try:
        conn.execute(
            'UPDATE players SET nickname=?, phone=?, age_group=?, position=? WHERE id=?',
            (nickname, phone, age_group, position, player_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_player(player_id):
    conn = get_conn()
    try:
        conn.execute('DELETE FROM players WHERE id=?', (player_id,))
        conn.commit()
    finally:
        conn.close()


def list_camps():
    conn = get_conn()
    try:
        rows = conn.execute('''
            SELECT c.*, 
                   (SELECT COUNT(*) FROM registrations r WHERE r.camp_id = c.id) as registered_count
            FROM camps c 
            ORDER BY c.id DESC
        ''').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def add_camp(name, start_date, end_date, fee, max_capacity, status='报名中'):
    if status not in CAMP_STATUSES:
        raise ValueError(f'无效的状态，必须是: {", ".join(CAMP_STATUSES)}')
    conn = get_conn()
    try:
        cur = conn.execute(
            'INSERT INTO camps (name, start_date, end_date, fee, max_capacity, status) VALUES (?, ?, ?, ?, ?, ?)',
            (name, start_date, end_date, fee, max_capacity, status)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_camp(camp_id, name, start_date, end_date, fee, max_capacity, status):
    if status not in CAMP_STATUSES:
        raise ValueError(f'无效的状态，必须是: {", ".join(CAMP_STATUSES)}')
    conn = get_conn()
    try:
        conn.execute(
            'UPDATE camps SET name=?, start_date=?, end_date=?, fee=?, max_capacity=?, status=? WHERE id=?',
            (name, start_date, end_date, fee, max_capacity, status, camp_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_camp(camp_id):
    conn = get_conn()
    try:
        conn.execute('DELETE FROM camps WHERE id=?', (camp_id,))
        conn.commit()
    finally:
        conn.close()


def register_player(player_id, camp_id):
    conn = get_conn()
    try:
        conn.execute('BEGIN IMMEDIATE')

        camp = conn.execute('SELECT * FROM camps WHERE id=?', (camp_id,)).fetchone()
        if not camp:
            conn.rollback()
            return {'success': False, 'message': '营期不存在'}

        if camp['status'] != '报名中':
            conn.rollback()
            return {'success': False, 'message': '营期非报名中状态，无法报名'}

        count = conn.execute(
            'SELECT COUNT(*) FROM registrations WHERE camp_id=?', (camp_id,)
        ).fetchone()[0]
        if count >= camp['max_capacity']:
            conn.rollback()
            return {'success': False, 'message': '营期人数已满'}

        existing = conn.execute(
            'SELECT 1 FROM registrations WHERE player_id=? AND camp_id=?',
            (player_id, camp_id)
        ).fetchone()
        if existing:
            conn.rollback()
            return {'success': False, 'message': '该球员已报名此营期'}

        conn.execute(
            'INSERT INTO registrations (player_id, camp_id) VALUES (?, ?)',
            (player_id, camp_id)
        )
        conn.commit()
        return {'success': True, 'message': '报名成功'}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': f'报名失败: {str(e)}'}
    finally:
        conn.close()


def list_registrations():
    conn = get_conn()
    try:
        rows = conn.execute('''
            SELECT r.*, p.nickname, p.age_group, c.name as camp_name
            FROM registrations r
            JOIN players p ON r.player_id = p.id
            JOIN camps c ON r.camp_id = c.id
            ORDER BY r.id DESC
        ''').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def checkin_player(player_id, camp_id):
    conn = get_conn()
    try:
        conn.execute('BEGIN IMMEDIATE')

        camp = conn.execute('SELECT * FROM camps WHERE id=?', (camp_id,)).fetchone()
        if not camp:
            conn.rollback()
            return {'success': False, 'message': '营期不存在'}

        if camp['status'] != '进行中':
            conn.rollback()
            return {'success': False, 'message': '营期非进行中状态，无法签到'}

        registered = conn.execute(
            'SELECT 1 FROM registrations WHERE player_id=? AND camp_id=?',
            (player_id, camp_id)
        ).fetchone()
        if not registered:
            conn.rollback()
            return {'success': False, 'message': '该球员未报名此营期'}

        today = datetime.now().strftime('%Y-%m-%d')
        existing = conn.execute(
            'SELECT 1 FROM checkins WHERE player_id=? AND camp_id=? AND checkin_date=?',
            (player_id, camp_id, today)
        ).fetchone()
        if existing:
            conn.rollback()
            return {'success': False, 'message': '该球员今日已在此营期签到'}

        conn.execute(
            'INSERT INTO checkins (player_id, camp_id, checkin_date) VALUES (?, ?, ?)',
            (player_id, camp_id, today)
        )
        conn.commit()
        return {'success': True, 'message': '签到成功'}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': f'签到失败: {str(e)}'}
    finally:
        conn.close()


def list_checkins():
    conn = get_conn()
    try:
        rows = conn.execute('''
            SELECT ci.*, p.nickname, p.age_group, c.name as camp_name
            FROM checkins ci
            JOIN players p ON ci.player_id = p.id
            JOIN camps c ON ci.camp_id = c.id
            ORDER BY ci.id DESC
        ''').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_player_monthly_checkins(player_id):
    conn = get_conn()
    try:
        now = datetime.now()
        month_start = now.strftime('%Y-%m-01')
        next_month = (now.replace(month=now.month % 12 + 1, year=now.year + (1 if now.month == 12 else 0))).strftime('%Y-%m-01')

        count = conn.execute('''
            SELECT COUNT(*) FROM checkins
            WHERE player_id=? AND checkin_date >= ? AND checkin_date < ?
        ''', (player_id, month_start, next_month)).fetchone()[0]

        return {'player_id': player_id, 'month': now.strftime('%Y-%m'), 'count': count}
    finally:
        conn.close()


def get_monthly_registration_by_age_group():
    conn = get_conn()
    try:
        now = datetime.now()
        month_start = now.strftime('%Y-%m-01')
        next_month = (now.replace(month=now.month % 12 + 1, year=now.year + (1 if now.month == 12 else 0))).strftime('%Y-%m-01')

        rows = conn.execute('''
            SELECT p.age_group, COUNT(*) as count
            FROM registrations r
            JOIN players p ON r.player_id = p.id
            WHERE r.created_at >= ? AND r.created_at < ?
            GROUP BY p.age_group
            ORDER BY p.age_group
        ''', (month_start, next_month)).fetchall()

        result = {age: 0 for age in AGE_GROUPS}
        for row in rows:
            result[row['age_group']] = row['count']

        return {'month': now.strftime('%Y-%m'), 'stats': result}
    finally:
        conn.close()
