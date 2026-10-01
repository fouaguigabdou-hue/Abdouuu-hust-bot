const express = require('express');
const mongoose = require('mongoose');
const multer = require('multer');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const Docker = require('dockerode');
const { v4: uuidv4 } = require('uuid');
const http = require('http');
const socketIo = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);
const docker = new Docker({ socketPath: '/var/run/docker.sock' });

app.use(express.json());
app.use(express.static('public'));

// ============ اتصال MongoDB ============
mongoose.connect('mongodb://localhost:27017/abdouuu_vps', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// ============ قاعدة البيانات ============
const UserSchema = new mongoose.Schema({
    key: { type: String, unique: true },
    username: String,
    expiry: Date,
    maxBots: { type: Number, default: 2 },
    ramLimit: { type: Number, default: 256 }, // MB
    bots: [{
        botId: String,
        name: String,
        containerId: String,
        status: String,
        language: String,
        createdAt: { type: Date, default: Date.now }
    }],
    createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', UserSchema);

// ============ رفع الملفات ============
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const userDir = `./uploads/${req.body.userKey}`;
        if (!fs.existsSync(userDir)) fs.mkdirSync(userDir, { recursive: true });
        cb(null, userDir);
    },
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}_${file.originalname}`);
    }
});

const upload = multer({ storage, limits: { fileSize: 50 * 1024 * 1024 } });

// ============ توليد كود ============
function generateKey() {
    const rand = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `ABDOUUU-VPS-HUSTENG-${rand}`;
}

// ============ 1. تسجيل الدخول ============
app.post('/api/login', async (req, res) => {
    const { key } = req.body;
    const user = await User.findOne({ key });
    
    if (!user) return res.status(401).json({ success: false, message: 'كود غير صحيح' });
    if (new Date() > user.expiry) return res.status(403).json({ success: false, message: 'انتهت الصلاحية' });
    
    res.json({ success: true, user });
});

// ============ 2. دخول الأدمن ============
const ADMIN_KEY = 'ADMIN_MASTER_KEY_2024'; // غيّرها لاحقاً

app.post('/api/admin/login', (req, res) => {
    const { key } = req.body;
    if (key === ADMIN_KEY) {
        res.json({ success: true, message: 'مرحباً أيها الأدمن' });
    } else {
        res.status(403).json({ success: false, message: 'غير مصرح' });
    }
});

// ============ 3. إنشاء كود (أدمن) ============
app.post('/api/admin/create-key', async (req, res) => {
    const { maxBots, durationDays, ramLimit } = req.body;
    const newKey = generateKey();
    const expiry = new Date();
    expiry.setDate(expiry.getDate() + parseInt(durationDays));

    const user = new User({
        key: newKey,
        expiry,
        maxBots: maxBots || 2,
        ramLimit: ramLimit || 256
    });
    await user.save();
    res.json({ success: true, key: newKey });
});

// ============ 4. جلب كل المستخدمين (أدمن) ============
app.get('/api/admin/users', async (req, res) => {
    const users = await User.find().sort({ createdAt: -1 });
    res.json(users);
});

// ============ 5. حذف مستخدم (أدمن) ============
app.delete('/api/admin/user/:key', async (req, res) => {
    const user = await User.findOne({ key: req.params.key });
    if (!user) return res.status(404).json({ message: 'غير موجود' });

    // إيقاف كل بوتات المستخدم
    for (const bot of user.bots) {
        if (bot.containerId) {
            try {
                const container = docker.getContainer(bot.containerId);
                await container.stop();
                await container.remove();
            } catch (e) {}
        }
    }
    await User.deleteOne({ key: req.params.key });
    res.json({ success: true });
});

// ============ 6. رفع بوت وتشغيله ============
app.post('/api/bot/upload', upload.single('botFile'), async (req, res) => {
    try {
        const { userKey, botName, language } = req.body;
        const user = await User.findOne({ key: userKey });
        
        if (!user) return res.status(401).json({ message: 'كود غير صحيح' });
        if (user.bots.length >= user.maxBots) return res.status(403).json({ message: 'وصلت للحد الأقصى' });

        const botId = uuidv4();
        const userDir = `/var/www/abdouuu-vps/uploads/${userKey}`;
        const filePath = req.file.path;

        // اختيار الصورة المناسبة
        let image, cmd;
        if (language === 'python') {
            image = 'python:3.10-slim';
            cmd = ['sh', '-c', `pip install -r requirements.txt 2>/dev/null; python ${path.basename(filePath)}`];
        } else {
            image = 'node:18-slim';
            cmd = ['sh', '-c', `npm install 2>/dev/null; node ${path.basename(filePath)}`];
        }

        // إنشاء حاوية Docker
        const container = await docker.createContainer({
            Image: image,
            Cmd: cmd,
            name: `bot_${botId}`,
            WorkingDir: '/app',
            HostConfig: {
                Memory: user.ramLimit * 1024 * 1024,
                NanoCpus: 500000000, // 0.5 CPU
                Binds: [`${userDir}:/app`],
                RestartPolicy: { Name: 'unless-stopped' },
                NetworkMode: 'bridge'
            },
            Tty: true
        });

        await container.start();

        // حفظ في قاعدة البيانات
        user.bots.push({
            botId,
            name: botName,
            containerId: container.id,
            status: 'running',
            language
        });
        await user.save();

        res.json({ success: true, botId, message: 'تم تشغيل البوت بنجاح' });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'خطأ: ' + error.message });
    }
});

// ============ 7. إيقاف بوت ============
app.post('/api/bot/stop', async (req, res) => {
    const { userKey, botId } = req.body;
    const user = await User.findOne({ key: userKey });
    if (!user) return res.status(401).json({ message: 'غير مصرح' });

    const bot = user.bots.find(b => b.botId === botId);
    if (!bot) return res.status(404).json({ message: 'البوت غير موجود' });

    try {
        const container = docker.getContainer(bot.containerId);
        await container.stop();
        bot.status = 'stopped';
        await user.save();
        res.json({ success: true });
    } catch (e) {
        res.status(500).json({ message: e.message });
    }
});

// ============ 8. تشغيل بوت متوقف ============
app.post('/api/bot/start', async (req, res) => {
    const { userKey, botId } = req.body;
    const user = await User.findOne({ key: userKey });
    const bot = user.bots.find(b => b.botId === botId);

    try {
        const container = docker.getContainer(bot.containerId);
        await container.start();
        bot.status = 'running';
        await user.save();
        res.json({ success: true });
    } catch (e) {
        res.status(500).json({ message: e.message });
    }
});

// ============ 9. حذف بوت ============
app.post('/api/bot/delete', async (req, res) => {
    const { userKey, botId } = req.body;
    const user = await User.findOne({ key: userKey });
    const botIndex = user.bots.findIndex(b => b.botId === botId);

    try {
        const container = docker.getContainer(user.bots[botIndex].containerId);
        await container.stop().catch(() => {});
        await container.remove().catch(() => {});
        user.bots.splice(botIndex, 1);
        await user.save();
        res.json({ success: true });
    } catch (e) {
        res.status(500).json({ message: e.message });
    }
});

// ============ 10. جلب سجلات البوت (Logs) ============
app.get('/api/bot/logs/:userKey/:botId', async (req, res) => {
    const user = await User.findOne({ key: req.params.userKey });
    const bot = user.bots.find(b => b.botId === req.params.botId);
    
    try {
        const container = docker.getContainer(bot.containerId);
        const logs = await container.logs({ stdout: true, stderr: true, tail: 100 });
        res.json({ logs: logs.toString('utf-8') });
    } catch (e) {
        res.status(500).json({ message: e.message });
    }
});

// ============ تشغيل السيرفر ============
server.listen(3000, () => {
    console.log('🚀 ABDOUUU HUSTENG VPS running on port 3000');
});