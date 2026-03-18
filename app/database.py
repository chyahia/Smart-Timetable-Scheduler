import sqlite3
from flask import g
import os
import sys

def get_smart_db_path(db_name="schedule_database.db", app_folder_name="SmartTimetableScheduler"):
    """
    دالة ذكية تحدد مسار قاعدة البيانات أينما كان التطبيق يعمل.
    إذا كان المجلد محمياً (مثل Program Files)، تقوم بإنشاء المسار في AppData.
    """
    # 1. تحديد المجلد الرئيسي (سواء كان exe أو مجلد المشروع أثناء التطوير)
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        # يرجع خطوتين للخلف لأن هذا الملف موجود داخل app/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    local_db_path = os.path.join(base_dir, db_name)

    # 2. اختبار صلاحية الكتابة في المجلد الحالي
    try:
        test_file = os.path.join(base_dir, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # إذا وصلنا هنا، يعني المجلد غير محمي، نستخدم المسار المحلي!
        return local_db_path

    except (IOError, OSError, PermissionError):
        # 3. المجلد محمي، ننتقل فوراً إلى مسار المستخدم (AppData/Roaming)
        appdata_dir = os.getenv('APPDATA')
        safe_app_dir = os.path.join(appdata_dir, app_folder_name)
        
        # إنشاء المجلد الخاص بالبرنامج إذا لم يكن موجوداً
        if not os.path.exists(safe_app_dir):
            os.makedirs(safe_app_dir)
            
        # إرجاع المسار الآمن الجديد في AppData
        return os.path.join(safe_app_dir, db_name)

# يتم تحديد المسار الذكي مرة واحدة عند استدعاء هذا الملف
DATABASE_FILE = get_smart_db_path()

def get_db_connection():
    """تنشئ أو تجلب الاتصال الحالي بقاعدة البيانات."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_FILE)
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """إغلاق قاعدة البيانات بعد انتهاء الطلب."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """دالة مساعدة لجلب البيانات (SELECT)"""
    conn = get_db_connection()
    cur = conn.execute(query, args)
    rv = [dict(row) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """دالة مساعدة لتنفيذ التعديلات (INSERT, UPDATE, DELETE)"""
    conn = get_db_connection()
    conn.execute(query, args)
    conn.commit()

def init_db(app):
    """إنشاء الجداول الأساسية عند بدء تشغيل الخادم."""
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # إنشاء الجداول الأساسية تماماً كما في مشروعك القديم
        cursor.execute('''CREATE TABLE IF NOT EXISTS levels (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, type TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, room_type TEXT NOT NULL, teacher_id INTEGER, FOREIGN KEY (teacher_id) REFERENCES teachers (id) ON DELETE SET NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS course_levels (course_id INTEGER, level_id INTEGER, PRIMARY KEY (course_id, level_id), FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE, FOREIGN KEY (level_id) REFERENCES levels (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
        
        conn.commit()