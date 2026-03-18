import webbrowser # أضف هذا في الأعلى
from app import create_app

app = create_app()

if __name__ == '__main__':
    # 1. تحديث الرابط ليفتح على المنفذ الجديد
    webbrowser.open("http://127.0.0.1:5050") 
    
    # 2. إخبار Flask باستخدام المنفذ 5050 بدلاً من 5000 الافتراضي
    app.run(host='127.0.0.1', port=5050, debug=False)