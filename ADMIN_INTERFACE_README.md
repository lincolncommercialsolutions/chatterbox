# 🎛️ Chatterbox Admin Interface - Quick Start

## 🚀 New Feature: Visual Voice & Character Management

Your Chatterbox TTS system now includes a **complete web-based admin interface** for managing voices and characters visually!

### 📱 Access the Admin Panel

**Local Development:**
```
http://localhost:5000/admin
```

**Deployed (Render/Railway/etc):**
```
https://your-app.onrender.com/admin
```

---

## ✨ What You Can Do

### 🎵 **Voice Management**
- **Upload voice samples** (drag & drop WAV/MP3/FLAC files)
- **View all voices** with usage information  
- **Test voices** with live audio playback
- **Delete unused voices** (safety protection included)

### 🤖 **Character Management**
- **Create new characters** with any voice
- **Visual parameter tuning** (exaggeration, temperature, CFG weight)
- **Test character voices** instantly
- **Assign custom emojis & colors**

### ⚙️ **Real-time Configuration**
- **No server restart** needed - changes are live immediately
- **Automatic S3 upload** for voice samples
- **Persistent configuration** saves to `character_voices.json`
- **Mobile responsive** design works on all devices

---

## 🎯 Quick Demo (3 Minutes)

### 1. **Upload a Voice Sample** (1 min)
1. Open `/admin` in your browser
2. Click **"⬆️ Upload Voice"** tab
3. **Drag & drop** a 3-5 second audio file (your voice saying something clear)
4. Fill in: Voice ID: `my_voice`, Name: `My Voice`
5. Click **"⬆️ Upload Voice"** ✅

### 2. **Create a Character** (1 min)
1. Click **"✨ Create Character"** tab
2. Fill in: Character ID: `my_character`, Name: `My Character`
3. **Select your uploaded voice** from dropdown
4. **Adjust sliders** for speech style (try exaggeration: 0.7 for more expressive)
5. Click **"✨ Create Character"** ✅

### 3. **Test Your Character** (1 min)  
1. Click **"🤖 Characters"** tab
2. Find your character and click **"🎵 Test"**
3. **Listen** to the generated audio - it should sound like your voice! 🎉
4. Try different parameter values to fine-tune the style

---

## 🔧 Deploy the Admin Interface

### If You Haven't Deployed Yet:
```bash
# Push to GitHub with admin interface
chmod +x deploy_admin.sh
./deploy_admin.sh

# Follow RENDER_DEPLOYMENT.md to deploy to Render
```

### If Already Deployed:
```bash
# Just push the new admin interface
git add .
git commit -m "Add admin interface"
git push origin main

# Render auto-deploys in ~2-3 minutes
```

---

## 📋 Feature Overview

| Feature | Description | Access |
|---------|-------------|---------|
| **Voice Library** | View, test, and manage all voices | `/admin` → Voices tab |
| **Character Profiles** | View and test all characters | `/admin` → Characters tab |
| **Upload Voice** | Add new voice samples via drag & drop | `/admin` → Upload tab |
| **Create Character** | Build characters with visual parameter tuning | `/admin` → Create tab |
| **Live Testing** | Generate and play audio instantly | Click 🎵 Test on any voice/character |
| **Safety Features** | Prevent deleting voices in use by characters | Automatic checks |
| **S3 Integration** | Automatic upload and public URL generation | Seamless background process |

---

## 🎨 Admin Interface Screenshots

The interface includes:
- **🎭 Modern design** with gradient backgrounds and smooth animations
- **📱 Mobile responsive** - works perfectly on phones/tablets
- **🎛️ Visual parameter sliders** with real-time value updates
- **🎵 Integrated audio players** for instant testing
- **📤 Drag & drop file upload** with visual feedback
- **🎨 Character customization** with emoji and color pickers
- **⚡ Live updates** without page refreshes

---

## 🔗 Integration with Your App

Characters created in the admin interface are **immediately available** in your API:

```javascript
// Use your custom character in your Vercel app
const response = await fetch('/generate-audio', {
  method: 'POST', 
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "Hello from my custom character!",
    character: "my_character"  // ← Created in admin interface
  })
});

const data = await response.json();
// Play data.audio in your chat UI
```

**No code changes needed** - new characters work with your existing TTS integration immediately!

---

## 📚 Documentation

- **[ADMIN_INTERFACE_GUIDE.md](ADMIN_INTERFACE_GUIDE.md)** - Complete admin interface documentation
- **[HOW_TO_ADD_VOICES.md](HOW_TO_ADD_VOICES.md)** - Voice setup guide (includes CLI methods)
- **[VOICE_MANAGEMENT.md](VOICE_MANAGEMENT.md)** - Advanced voice system documentation

---

## 🆘 Quick Troubleshooting

### "Admin interface won't load"
```bash
# Check if server is running
curl http://localhost:5000/health

# Check API endpoints
curl http://localhost:5000/admin/voices
```

### "Upload fails" 
- Check AWS credentials in `.env` file
- Verify S3 bucket permissions
- Try smaller file size (< 10MB)

### "Character not working"
- Refresh admin interface
- Check voice was uploaded successfully
- Test voice generation first

---

## ⭐ Pro Tips

### **Voice Quality Tips:**
- Use **3-5 second** clear audio samples
- **Single speaker** only (no background noise)
- **Natural speech** works better than overly dramatic 
- **WAV format** gives best quality (MP3/FLAC also supported)

### **Character Parameters:**
- **Exaggeration 0.4-0.6**: Balanced, natural speech
- **Exaggeration 0.7+**: More expressive, animated style
- **Temperature 0.6-0.8**: Natural variation, recommended
- **CFG Weight 0.5-0.7**: Good balance of quality and variety

### **Organization:**
- Use **descriptive Voice IDs** (e.g., `male_narrator`, `female_friendly`)
- Add **tags** to voice samples (e.g., `male`, `calm`, `professional`)
- Keep **consistent naming** for characters (e.g., `assistant_en`, `assistant_es`)

---

## 🎉 You're Ready!

The admin interface makes voice and character management **incredibly easy**. No more editing JSON files or command-line uploads!

**Open `/admin` and start building amazing custom voices for your TTS system! 🎙️**