from flask import Flask, jsonify, request, render_template, redirect, url_for, send_file
from pymongo import MongoClient
import gridfs
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# الاتصال بقاعدة البيانات
client = MongoClient("mongodb+srv://a771415:771415164Aa@phone.avried4.mongodb.net/?retryWrites=true&w=majority")
db_name = "phones_db"
collection_name = "phones"
db = client[db_name]

# إنشاء المجلد لرفع الملفات إذا لم يكن موجودًا
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    try:
        client.admin.command('ping')
        status = "متصل بقاعدة البيانات بنجاح!"
    except Exception as e:
        status = f"فشل في الاتصال بقاعدة البيانات: {e}"
        return render_template('index.html', status=status), 500

    db_list = client.list_database_names()
    if db_name not in db_list:
        collection = db[collection_name]
        status += f" قاعدة البيانات {db_name} غير موجودة، سيتم إنشاؤها الآن."
        sample_data = {
            "Phone Type": "",
            "Issue Type": "",
            "Phone Name": "",
            "Baseband": "",
            "Version": "",
            "CSC": "",
            "problm": "",
            "fixproblm": "",
            "file": None
        }
        collection.insert_one(sample_data)
        status += " تم إدراج عينة بيانات للتأكد من إنشاء الأعمدة."
    else:
        status += f" قاعدة البيانات {db_name} موجودة."

    return render_template('index.html', status=status)

@app.route('/data', methods=['GET', 'POST'])
def get_data():
    collection = db[collection_name]
    
    query = {}
    if request.method == 'POST':
        search_term = request.form['search'].strip()
        if search_term:
            query = {"$or": [
                {"Phone Type": {"$regex": search_term, "$options": "i"}},
                {"Issue Type": {"$regex": search_term, "$options": "i"}},
                {"Phone Name": {"$regex": search_term, "$options": "i"}},
                {"Baseband": {"$regex": search_term, "$options": "i"}},
                {"Version": {"$regex": search_term, "$options": "i"}},
                {"CSC": {"$regex": search_term, "$options": "i"}},
                {"problm": {"$regex": search_term, "$options": "i"}},
                {"fixproblm": {"$regex": search_term, "$options": "i"}}
            ]}
    
    data = list(collection.find(query, {"_id": 0}))  # استرجاع جميع البيانات بدون حقل _id
    return render_template('data.html', data=data)

@app.route('/add', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        phone_type = request.form['phone_type']
        issue_type = request.form['issue_type']
        phone_name = request.form['phone_name']
        baseband = request.form['baseband']
        version = request.form['version']
        csc = request.form['csc']
        problm = request.form['problm']
        fixproblm = request.form['fixproblm']
        file = request.files['file']
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            fs = gridfs.GridFS(db)
            file_id = fs.put(open(file_path, 'rb'), filename=filename)
        else:
            file_id = None

        collection = db[collection_name]
        data = {
            "Phone Type": phone_type,
            "Issue Type": issue_type,
            "Phone Name": phone_name,
            "Baseband": baseband,
            "Version": version,
            "CSC": csc,
            "problm": problm,
            "fixproblm": fixproblm,
            "file": file_id
        }
        collection.insert_one(data)
        return redirect(url_for('get_data'))
    return render_template('add.html')

@app.route('/file/<file_id>')
def get_file(file_id):
    fs = gridfs.GridFS(db)
    try:
        file = fs.get(file_id)
        return send_file(file, download_name=file.filename, as_attachment=True)
    except gridfs.errors.NoFile:
        return "الملف غير موجود.", 404

if __name__ == '__main__':
    app.run(debug=True)
