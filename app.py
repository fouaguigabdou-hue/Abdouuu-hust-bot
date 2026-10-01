from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os, uuid, random, string, subprocess, json, threading, zipfile, shutil

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DATA_FILE = os.path.join(BASE_DIR, 'data.json')
ADMIN_SECRET_URL = 'abdouuu-admin-ghost'
INSTAGRAM_USER = 'zi.wr'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

data_lock = threading.Lock()

# ============ التخزين ============
def load_data():
    if not os.path.exists(DATA_FILE):
        return {'users': {}}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'users': {}}

def save_data(data):
    with data_lock:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# ============ Docker ============
USE_DOCKER = False
docker_client = None
try:
    import docker
    docker_client = docker.from_env()
    docker_client.ping()
    USE_DOCKER = True
    print("✅ Docker Mode (VPS)")
except Exception:
    print("📱 Termux Mode (subprocess)")

running_processes = {}

# ============ خريطة المكتبات (اسم الاستيراد → اسم pip) ============
PIP_MAP = {
    'telebot': 'pyTelegramBotAPI',
    'telegram': 'python-telegram-bot',
    'discord': 'discord.py',
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'crypto': 'pycryptodome',
    'Crypto': 'pycryptodome',
    'flask': 'Flask',
    'requests': 'requests',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'selenium': 'selenium',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'aiohttp': 'aiohttp',
    'psutil': 'psutil',
    'colorama': 'colorama',
    'rich': 'rich',
    'qrcode': 'qrcode',
    'pyautogui': 'pyautogui',
    'pynput': 'pynput',
    'pyttsx3': 'pyttsx3',
    'speech_recognition': 'SpeechRecognition',
    'wikipedia': 'wikipedia',
    'youtube_dl': 'youtube-dl',
    'pytube': 'pytube',
    'instagrapi': 'instagrapi',
    'twilio': 'twilio',
    'openai': 'openai',
    'gtts': 'gTTS',
    'playsound': 'playsound',
    'pygame': 'pygame',
    'keyboard': 'keyboard',
    'mouse': 'mouse',
    'pyperclip': 'pyperclip',
    'googletrans': 'googletrans==4.0.0-rc1',
    'translate': 'translate',
    'googlesearch': 'googlesearch-python',
    'pywhatkit': 'pywhatkit',
    'whatsapp': 'pywhatkit',
    'werkzeug': 'Werkzeug',
    'jinja2': 'Jinja2',
    'sqlalchemy': 'SQLAlchemy',
    'redis': 'redis',
    'pymongo': 'pymongo',
    'mysql': 'mysql-connector-python',
    'psycopg2': 'psycopg2-binary',
    'jwt': 'PyJWT',
    'passlib': 'passlib',
    'bcrypt': 'bcrypt',
    'stegano': 'stegano',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'plotly': 'plotly',
    'scipy': 'scipy',
    'tensorflow': 'tensorflow',
    'torch': 'torch',
    'keras': 'keras',
    'transformers': 'transformers',
    'imageio': 'imageio',
    'moviepy': 'moviepy',
    'ffmpeg': 'ffmpeg-python',
    'pydub': 'pydub',
    'fpdf': 'fpdf',
    'reportlab': 'reportlab',
    'docx': 'python-docx',
    'openpyxl': 'openpyxl',
    'pdfplumber': 'pdfplumber',
    'tabulate': 'tabulate',
    'emoji': 'emoji',
    'regex': 'regex',
    'dateutil': 'python-dateutil',
    'pytz': 'pytz',
    'tzlocal': 'tzlocal',
    'schedule': 'schedule',
    'apscheduler': 'APScheduler',
    'celery': 'celery',
    'tqdm': 'tqdm',
    'click': 'click',
    'tabulate_': 'tabulate',
    'termcolor': 'termcolor',
    'halo': 'halo',
    'colorlog': 'colorlog',
    'logging_': 'logging',
    'pyfiglet': 'pyfiglet',
    'art': 'art',
    'faker': 'Faker',
    'nanoid': 'nanoid',
    'shortuuid': 'shortuuid',
    'humanize': 'humanize',
    'inflect': 'inflect',
    'num2words': 'num2words',
    'translate_': 'translate',
    'arabic_reshaper': 'arabic-reshaper',
    'bidi': 'python-bidi',
    'python_bidi': 'python-bidi',
    'arabic': 'arabic-reshaper'
}

# مكتبات مدمجة (لا تحتاج تثبيت)
BUILTIN_MODULES = {
    'os','sys','time','datetime','math','random','re','socket','threading',
    'subprocess','shutil','glob','csv','urllib','http','base64','hashlib',
    'hmac','secrets','uuid','logging','argparse','collections','itertools',
    'functools','typing','dataclasses','pathlib','io','string','pprint',
    'traceback','json','pickle','sqlite3','tkinter','winsound','asyncio',
    'concurrent','multiprocessing','queue','signal','atexit','contextlib',
    'copy','enum','gc','inspect','marshal','platform','statistics','warnings',
    'weakref','abc','array','bisect','calendar','cmath','codecs','decimal',
    'difflib','email','ftplib','getpass','gettext','gzip','html','imaplib',
    'ipaddress','keyword','locale','mimetypes','numbers','operator','optparse',
    'pdb','plistlib','poplib','profile','pstats','pty','pwd','py_compile',
    'pydoc','quopri','runpy','sched','shelve','smtplib','sndhdr','stat',
    'struct','symtable','tabnanny','tarfile','telnetlib','tempfile','textwrap',
    'timeit','token','tokenize','turtle','types','unicodedata','unittest',
    'uu','wave','webbrowser','wsgiref','xml','xmlrpc','zipapp','zipfile',
    'zlib','__future__','ast','builtins','cgi','cgitb','cmd','code','codeop',
    'colorsys','compileall','configparser','crypt','ctypes','termios','tty',
    'tty_','select','selectors','ssl','socket','socketserver','http.server'
}

def extract_imports(file_path):
    """يستخرج كل المكتبات المستوردة في ملف Python"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                continue
            # import xxx
            if line.startswith('import '):
                parts = line.replace('import ', '').split(',')
                for p in parts:
                    mod = p.strip().split(' as ')[0].strip().split('.')[0]
                    if mod and mod.isidentifier():
                        imports.add(mod)
            # from xxx import yyy
            elif line.startswith('from '):
                parts = line.replace('from ', '').split(' import ')
                if parts:
                    mod = parts[0].strip().split('.')[0]
                    if mod and mod.isidentifier():
                        imports.add(mod)
    except Exception as e:
        print(f"Extract imports error: {e}")
    return imports

def get_pip_packages(file_path):
    """يرجع قائمة حزم pip المطلوبة"""
    imports = extract_imports(file_path)
    packages = set()
    
    for imp in imports:
        if imp in BUILTIN_MODULES:
            continue
        if imp.startswith('_'):
            continue
        # استخدام الخريطة إن وُجدت
        if imp in PIP_MAP:
            packages.add(PIP_MAP[imp])
        else:
            packages.add(imp)
    
    return list(packages)

def detect_main_candidates(directory, language):
    exts = ['.py'] if language == 'python' else ['.js']
    preferred = ['main','bot','app','index','start','run','launch']
    candidates = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ('node_modules','__pycache__','venv','.git','.venv')]
        for f in files:
            if any(f.endswith(e) for e in exts):
                rel = os.path.relpath(os.path.join(root, f), directory)
                fname = f.lower()
                score = 0
                for i, p in enumerate(preferred):
                    if fname.startswith(p):
                        score = 100 - i
                        break
                    elif p in fname:
                        score = max(score, 50 - i)
                candidates.append({'path': rel, 'score': score})
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return [c['path'] for c in candidates]

# ============ الصفحات ============
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/dashboard.html')
def dashboard():
    return send_from_directory('public', 'dashboard.html')

@app.route(f'/{ADMIN_SECRET_URL}')
def admin_page():
    return send_from_directory('public', 'admin.html')

# ============ API: الدخول ============
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    if not key:
        return jsonify({'success': False, 'message': 'أدخل الكود'}), 400
    all_data = load_data()
    user = all_data['users'].get(key)
    if not user:
        return jsonify({'success': False, 'message': '❌ كود غير صحيح'}), 401
    if datetime.now() > datetime.fromisoformat(user['expiry']):
        return jsonify({'success': False, 'message': '⏰ انتهت الصلاحية'}), 403
    user['_id'] = key
    return jsonify({'success': True, 'user': user})

# ============ API: الأدمن ============
@app.route('/api/admin/create-key', methods=['POST'])
def create_key():
    data = request.get_json() or {}
    max_bots = int(data.get('maxBots', 2))
    max_users = int(data.get('maxUsers', 1))
    duration_days = int(data.get('durationDays', 30))
    ram_limit = int(data.get('ramLimit', 256))
    
    new_key = generate_key()
    expiry = datetime.now() + timedelta(days=duration_days)
    
    all_data = load_data()
    all_data['users'][new_key] = {
        'key': new_key,
        'expiry': expiry.isoformat(),
        'maxBots': max_bots,
        'maxUsers': max_users,
        'ramLimit': ram_limit,
        'bots': [],
        'createdAt': datetime.now().isoformat()
    }
    save_data(all_data)
    return jsonify({'success': True, 'key': new_key})

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    all_data = load_data()
    users = list(all_data['users'].values())
    users.sort(key=lambda u: u.get('createdAt',''), reverse=True)
    return jsonify(users)

@app.route('/api/admin/user/<key>', methods=['DELETE'])
def delete_user(key):
    all_data = load_data()
    user = all_data['users'].get(key)
    if not user:
        return jsonify({'message': 'غير موجود'}), 404
    for bot in user.get('bots', []):
        if USE_DOCKER and bot.get('containerId'):
            try:
                c = docker_client.containers.get(bot['containerId'])
                c.stop(timeout=5); c.remove()
            except Exception: pass
        elif bot.get('botId') in running_processes:
            try:
                running_processes[bot['botId']].terminate()
                del running_processes[bot['botId']]
            except Exception: pass
    user_dir = os.path.join(UPLOAD_FOLDER, key)
    if os.path.exists(user_dir):
        try: shutil.rmtree(user_dir)
        except Exception: pass
    del all_data['users'][key]
    save_data(all_data)
    return jsonify({'success': True})

@app.route('/api/admin/user-files/<key>', methods=['GET'])
def admin_user_files(key):
    user_dir = os.path.join(UPLOAD_FOLDER, key)
    if not os.path.exists(user_dir):
        return jsonify({'success': True, 'tree': []})
    tree = []
    for root, dirs, files in os.walk(user_dir):
        dirs[:] = [d for d in dirs if d not in ('node_modules','__pycache__','venv','.venv','.git')]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, user_dir)
            try: size = os.path.getsize(full)
            except: size = 0
            tree.append({'path': rel, 'name': f, 'size': size, 'depth': rel.count(os.sep)})
    tree.sort(key=lambda x: x['path'])
    return jsonify({'success': True, 'tree': tree[:500]})

@app.route('/api/admin/read-file', methods=['POST'])
def admin_read_file():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    path = data.get('path', '').strip()
    if not key or not path:
        return jsonify({'message': 'بيانات ناقصة'}), 400
    parts = [p for p in path.split('/') if p and p not in ('.', '..')]
    safe_path = os.path.join(UPLOAD_FOLDER, key, *parts)
    full_path = os.path.abspath(safe_path)
    base_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, key))
    if not full_path.startswith(base_path):
        return jsonify({'message': 'مسار غير مسموح'}), 403
    if not os.path.exists(full_path):
        return jsonify({'message': 'الملف غير موجود'}), 404
    try:
        size = os.path.getsize(full_path)
        if size > 2 * 1024 * 1024:
            return jsonify({'message': 'الملف كبير جداً'}), 400
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return jsonify({'success': True, 'content': content, 'size': size})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ============ API: فحص ZIP ============
@app.route('/api/bot/inspect-zip', methods=['POST'])
def inspect_zip():
    if 'zipFile' not in request.files:
        return jsonify({'message': 'لا يوجد ملف'}), 400
    f = request.files['zipFile']
    if not f.filename.lower().endswith('.zip'):
        return jsonify({'message': 'الملف ليس ZIP'}), 400
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    tmp = os.path.join(UPLOAD_FOLDER, f'tmp_{uuid.uuid4().hex[:8]}.zip')
    f.save(tmp)
    try:
        with zipfile.ZipFile(tmp, 'r') as z:
            all_files = z.namelist()
        tree = []
        code_files = []
        has_requirements = False
        has_package = False
        requirements_path = None
        package_path = None
        for name in all_files:
            if name.endswith('/') or name.startswith('__MACOSX') or '/.git/' in name:
                continue
            depth = name.count('/')
            basename = name.split('/')[-1]
            is_code = basename.endswith('.py') or basename.endswith('.js')
            is_req = basename == 'requirements.txt'
            is_pkg = basename == 'package.json'
            if is_req:
                has_requirements = True
                requirements_path = name
            if is_pkg:
                has_package = True
                package_path = name
            if is_code:
                code_files.append({'path': name, 'name': basename, 'depth': depth, 'size': z.getinfo(name).file_size})
            tree.append({'path': name, 'name': basename, 'depth': depth, 'isCode': is_code, 'isReq': is_req, 'isPkg': is_pkg})
        preferred = ['main','bot','app','index','start','run','launch']
        suggested = None
        best_score = -1
        for cf in code_files:
            fname = cf['name'].lower().replace('.py','').replace('.js','')
            score = 0
            for i, p in enumerate(preferred):
                if fname == p:
                    score = 100 - i
                    break
                elif p in fname:
                    score = max(score, 50 - i)
            if score > best_score:
                best_score = score
                suggested = cf['path']
        os.remove(tmp)
        return jsonify({
            'success': True, 'tree': tree[:200], 'codeFiles': code_files,
            'hasRequirements': has_requirements, 'hasPackage': has_package,
            'requirementsPath': requirements_path, 'packagePath': package_path,
            'suggested': suggested, 'totalFiles': len(all_files)
        })
    except Exception as e:
        try: os.remove(tmp)
        except: pass
        return jsonify({'message': f'خطأ: {e}'}), 500

def generate_key():
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"ABDOUUU-VPS-HUSTENG-{rand}"

def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_to)
        return True
    except Exception as e:
        print(f"ZIP error: {e}")
        return False

# ============ API: رفع البوت (النسخة النهائية مع الكشف التلقائي) ============
@app.route('/api/bot/upload', methods=['POST'])
@app.route('/api/bot/upload-multi', methods=['POST'])
def upload_bot():
    try:
        user_key = request.form.get('userKey', '').strip()
        bot_name = request.form.get('botName', '').strip()
        language = request.form.get('language', 'python')
        main_file = request.form.get('mainFile', '').strip()
        
        all_data = load_data()
        user = all_data['users'].get(user_key)
        if not user:
            return jsonify({'message': '❌ كود غير صحيح'}), 401
        if len(user.get('bots', [])) >= user['maxBots']:
            return jsonify({'message': f'⚠️ وصلت للحد ({user["maxBots"]})'}), 403
        
        files = request.files.getlist('botFiles') or request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'message': 'لا توجد ملفات'}), 400
        
        bot_id = str(uuid.uuid4())
        work_dir = os.path.join(UPLOAD_FOLDER, user_key, bot_id)
        os.makedirs(work_dir, exist_ok=True)
        
        uploaded = []
        zip_files = []
        
        for f in files:
            if f.filename == '': continue
            rel_path = f.filename.replace('\\', '/')
            parts = [p for p in rel_path.split('/') if p and p not in ('.', '..')]
            if not parts: continue
            safe_rel = '/'.join(secure_filename(p) for p in parts)
            target = os.path.join(work_dir, safe_rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            f.save(target)
            uploaded.append(safe_rel)
            if safe_rel.lower().endswith('.zip'):
                zip_files.append(target)
        
        for zp in zip_files:
            extract_zip(zp, work_dir)
        
        req_file = None
        pkg_file = None
        for root, dirs, fs in os.walk(work_dir):
            dirs[:] = [d for d in dirs if d not in ('node_modules','__pycache__','venv','.git','.venv')]
            if 'requirements.txt' in fs and not req_file:
                req_file = os.path.relpath(os.path.join(root, 'requirements.txt'), work_dir)
            if 'package.json' in fs and not pkg_file:
                pkg_file = os.path.relpath(os.path.join(root, 'package.json'), work_dir)
        
        if main_file:
            final_main = main_file.strip().lstrip('/')
            if not os.path.exists(os.path.join(work_dir, final_main)):
                return jsonify({'message': f'الملف الرئيسي "{final_main}" غير موجود'}), 400
        else:
            candidates = detect_main_candidates(work_dir, language)
            if not candidates:
                return jsonify({'message': '❌ لم يُعثر على ملف .py أو .js'}), 400
            final_main = candidates[0]
        
        # ===== VPS Mode =====
        if USE_DOCKER:
            image = 'python:3.10-slim' if language == 'python' else 'node:18-slim'
            if language == 'python':
                if req_file:
                    cmd = f"sh -c 'pip install -r {req_file} 2>&1; python {final_main}'"
                else:
                    cmd = f"sh -c 'python {final_main}'"
            else:
                if pkg_file:
                    pkg_dir = os.path.dirname(pkg_file) or '.'
                    cmd = f"sh -c 'cd {pkg_dir} && npm install 2>&1; node {final_main}'"
                else:
                    cmd = f"sh -c 'node {final_main}'"
            
            container = docker_client.containers.run(
                image=image, command=cmd, name=f"bot_{bot_id}",
                working_dir='/app',
                volumes={work_dir: {'bind':'/app','mode':'rw'}},
                mem_limit=f"{user['ramLimit']}m",
                nano_cpus=500000000, detach=True,
                restart_policy={'Name':'unless-stopped'}, tty=True
            )
            container_id = container.id
            pid = None
            log_file = None
        
        # ===== Termux Mode =====
        else:
            main_path = os.path.join(work_dir, final_main)
            wd = os.path.dirname(main_path)
            mf = os.path.basename(main_path)
            log_file = os.path.join(work_dir, f"terminal.log")
            
            with open(log_file, 'w', encoding='utf-8') as lf:
                lf.write(f"""
╔══════════════════════════════════════════════════════════════╗
║   ABDOUUU VIP HOSTENG — TERMINAL LOG                         ║
║   Bot: {bot_name}
║   Language: {language}
║   Main: {final_main}
║   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
╚══════════════════════════════════════════════════════════════╝
""")
            
            # ===== تثبيت المكتبات (الكشف التلقائي) =====
            if language == 'python':
                # 1. تثبيت requirements.txt إن وُجد
                if req_file:
                    req_path = os.path.join(work_dir, req_file)
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        lf.write(f"\n[SETUP] Found requirements.txt: {req_file}\n")
                        lf.write(f"[SETUP] Installing dependencies from file...\n")
                        lf.write("─" * 60 + "\n")
                        lf.flush()
                    try:
                        install = subprocess.run(
                            ['pip', 'install', '-r', req_path],
                            capture_output=True, text=True, timeout=900, cwd=work_dir
                        )
                        with open(log_file, 'a', encoding='utf-8') as lf:
                            lf.write(install.stdout + "\n" + install.stderr)
                            lf.write("\n[SETUP] ✅ requirements.txt installed\n")
                    except Exception as ex:
                        with open(log_file, 'a', encoding='utf-8') as lf:
                            lf.write(f"\n[SETUP] ⚠️ Error: {ex}\n")
                
                # 2. الكشف التلقائي عن المكتبات
                try:
                    pkgs = get_pip_packages(main_path)
                except Exception:
                    pkgs = []
                
                # فحص كل ملفات .py في المجلد
                all_py_files = []
                for root, dirs, fs in os.walk(work_dir):
                    dirs[:] = [d for d in dirs if d not in ('node_modules','__pycache__','venv','.venv','.git')]
                    for f in fs:
                        if f.endswith('.py'):
                            all_py_files.append(os.path.join(root, f))
                
                all_imports = set()
                for pyf in all_py_files:
                    try:
                        all_imports |= extract_imports(pyf)
                    except Exception:
                        pass
                
                # ترجمة الاستيرادات إلى حزم pip
                pkgs_set = set()
                for imp in all_imports:
                    if imp in BUILTIN_MODULES or imp.startswith('_'):
                        continue
                    if imp in PIP_MAP:
                        if PIP_MAP[imp]:
                            pkgs_set.add(PIP_MAP[imp])
                    else:
                        pkgs_set.add(imp)
                
                if pkgs_set:
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        lf.write(f"\n[SETUP] Detected {len(pkgs_set)} external package(s):\n")
                        for pkg in sorted(pkgs_set):
                            lf.write(f"  → {pkg}\n")
                        lf.write("\n[SETUP] Auto-installing packages...\n")
                        lf.write("─" * 60 + "\n")
                        lf.flush()
                    
                    for pkg in sorted(pkgs_set):
                        if not pkg:
                            continue
                        try:
                            with open(log_file, 'a', encoding='utf-8') as lf:
                                lf.write(f"\n[PIP] Installing: {pkg}\n")
                                lf.flush()
                            install = subprocess.run(
                                ['pip', 'install', '--quiet', pkg],
                                capture_output=True, text=True, timeout=300
                            )
                            with open(log_file, 'a', encoding='utf-8') as lf:
                                if install.returncode == 0:
                                    lf.write(f"[PIP] ✅ {pkg} installed\n")
                                else:
                                    err = (install.stderr or '')[:300]
                                    lf.write(f"[PIP] ⚠️ {pkg} failed: {err}\n")
                        except Exception as ex:
                            with open(log_file, 'a', encoding='utf-8') as lf:
                                lf.write(f"[PIP] ❌ {pkg}: {ex}\n")
                    
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        lf.write("\n[SETUP] ✅ Auto-install complete\n")
                else:
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        lf.write("\n[SETUP] ✅ No external packages needed (builtin only)\n")
            
            # Node.js
            if language == 'node' and pkg_file:
                pkg_dir = os.path.dirname(os.path.join(work_dir, pkg_file))
                with open(log_file, 'a', encoding='utf-8') as lf:
                    lf.write(f"\n[SETUP] Found package.json: {pkg_file}\n")
                    lf.write(f"[SETUP] Installing npm packages...\n")
                    lf.write("─" * 60 + "\n")
                    lf.flush()
                try:
                    install = subprocess.run(
                        ['npm', 'install'],
                        capture_output=True, text=True, timeout=600, cwd=pkg_dir
                    )
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        lf.write(install.stdout + "\n" + install.stderr)
                        lf.write("\n[SETUP] ✅ Packages installed\n")
                except Exception as ex:
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        lf.write(f"\n[SETUP] ⚠️ Error: {ex}\n")
            
            with open(log_file, 'a', encoding='utf-8') as lf:
                lf.write(f"\n[LAUNCH] Running: {mf}\n")
                lf.write("═" * 60 + "\n\n")
                lf.flush()
            
            cmd = ['python3', '-u', mf] if language == 'python' else ['node', mf]
            log_handle = open(log_file, 'a', encoding='utf-8', buffering=1)
            process = subprocess.Popen(
                cmd, stdout=log_handle, stderr=subprocess.STDOUT, cwd=wd
            )
            running_processes[bot_id] = process
            container_id = None
            pid = process.pid
        
        user['bots'].append({
            'botId': bot_id,
            'name': bot_name,
            'containerId': container_id,
            'pid': pid,
            'logFile': log_file,
            'workDir': work_dir,
            'mainFile': final_main,
            'status': 'running',
            'language': language,
            'filesCount': len(uploaded),
            'isZip': len(zip_files) > 0,
            'requirements': req_file,
            'packageJson': pkg_file,
            'createdAt': datetime.now().isoformat()
        })
        save_data(all_data)
        
        return jsonify({
            'success': True,
            'botId': bot_id,
            'mainFile': final_main,
            'message': f'✅ تم التشغيل ({len(uploaded)} ملف)'
        })
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'message': f'خطأ: {str(e)}'}), 500

# ============ API: إيقاف/تشغيل/حذف ============
@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    data = request.get_json() or {}
    all_data = load_data()
    user = all_data['users'].get(data.get('userKey'))
    if not user: return jsonify({'message':'غير مصرح'}), 401
    bot = next((b for b in user.get('bots',[]) if b['botId']==data.get('botId')), None)
    if not bot: return jsonify({'message':'غير موجود'}), 404
    try:
        if USE_DOCKER and bot.get('containerId'):
            docker_client.containers.get(bot['containerId']).stop(timeout=5)
        elif bot['botId'] in running_processes:
            running_processes[bot['botId']].terminate()
            del running_processes[bot['botId']]
        bot['status'] = 'stopped'
        if bot.get('logFile') and os.path.exists(bot['logFile']):
            with open(bot['logFile'], 'a', encoding='utf-8') as lf:
                lf.write(f"\n[STOP] تم الإيقاف {datetime.now().strftime('%H:%M:%S')}\n")
        save_data(all_data)
        return jsonify({'success': True, 'message': '⏸ تم الإيقاف'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    data = request.get_json() or {}
    all_data = load_data()
    user = all_data['users'].get(data.get('userKey'))
    if not user: return jsonify({'message':'غير مصرح'}), 401
    bot = next((b for b in user.get('bots',[]) if b['botId']==data.get('botId')), None)
    if not bot: return jsonify({'message':'غير موجود'}), 404
    try:
        if USE_DOCKER and bot.get('containerId'):
            docker_client.containers.get(bot['containerId']).start()
        else:
            main_path = os.path.join(bot['workDir'], bot['mainFile'])
            wd = os.path.dirname(main_path)
            mf = os.path.basename(main_path)
            cmd = ['python3', '-u', mf] if bot['language']=='python' else ['node', mf]
            with open(bot['logFile'],'a', encoding='utf-8') as lf:
                lf.write(f"\n[START] تم التشغيل {datetime.now().strftime('%H:%M:%S')}\n")
            log_handle = open(bot['logFile'], 'a', encoding='utf-8', buffering=1)
            p = subprocess.Popen(cmd, stdout=log_handle, stderr=subprocess.STDOUT, cwd=wd)
            running_processes[bot['botId']] = p
        bot['status'] = 'running'
        save_data(all_data)
        return jsonify({'success': True, 'message': '▶ تم التشغيل'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/bot/delete', methods=['POST'])
def delete_bot():
    data = request.get_json() or {}
    all_data = load_data()
    user = all_data['users'].get(data.get('userKey'))
    if not user: return jsonify({'message':'غير مصرح'}), 401
    bot = next((b for b in user.get('bots',[]) if b['botId']==data.get('botId')), None)
    if not bot: return jsonify({'message':'غير موجود'}), 404
    try:
        if USE_DOCKER and bot.get('containerId'):
            c = docker_client.containers.get(bot['containerId'])
            try: c.stop(timeout=5)
            except: pass
            c.remove()
        elif bot['botId'] in running_processes:
            running_processes[bot['botId']].terminate()
            del running_processes[bot['botId']]
        wd = bot.get('workDir')
        if wd and os.path.exists(wd):
            try: shutil.rmtree(wd)
            except: pass
    except Exception as e:
        print(f"Delete error: {e}")
    user['bots'] = [b for b in user['bots'] if b['botId'] != data.get('botId')]
    save_data(all_data)
    return jsonify({'success': True, 'message': '🗑 تم الحذف'})

@app.route('/api/bot/logs/<user_key>/<bot_id>', methods=['GET'])
def bot_logs(user_key, bot_id):
    all_data = load_data()
    user = all_data['users'].get(user_key)
    if not user: return jsonify({'message':'غير مصرح'}), 401
    bot = next((b for b in user.get('bots',[]) if b['botId']==bot_id), None)
    if not bot: return jsonify({'message':'غير موجود'}), 404
    tail = request.args.get('tail', 500, type=int)
    try:
        if USE_DOCKER and bot.get('containerId'):
            c = docker_client.containers.get(bot['containerId'])
            logs = c.logs(stdout=True, stderr=True, tail=tail)
            return jsonify({'logs': logs.decode('utf-8', errors='replace')})
        elif bot.get('logFile') and os.path.exists(bot['logFile']):
            with open(bot['logFile'],'r',errors='replace') as f:
                lines = f.readlines()
            return jsonify({'logs': ''.join(lines[-tail:])})
        return jsonify({'logs':'لا توجد سجلات'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ============ التشغيل ============
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        save_data({'users': {}})
    print(f"\n{'='*60}")
    print(f"👻 ABDOUUU HOSTENG — GHOST MODE")
    print(f"{'='*60}")
    print(f"🌐 الموقع:      http://localhost:3000")
    print(f"👑 رابط الأدمن: http://localhost:3000/{ADMIN_SECRET_URL}")
    print(f"📷 انستغرام:    @{INSTAGRAM_USER}")
    print(f"📦 Auto-detect: مفعل (يكتشف المكتبات تلقائياً)")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=3000, debug=False)