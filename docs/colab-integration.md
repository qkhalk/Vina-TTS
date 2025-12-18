# Google Colab Integration Guide

## Overview

VieNeu-TTS supports **hybrid backend mode** - you can choose to run TTS processing on your local machine OR offload it to Google Colab's free GPU. This is useful when:

- **Your local machine has limited resources** → Use Colab's free T4 GPU
- **You want lower latency** → Use local mode if you have a capable GPU
- **Testing different configurations** → Easily switch between local and remote without restarting

## Key Features

✅ **Flexible Backend Selection** - Switch between Local and Google Colab anytime  
✅ **Both backends can be ready** - Have local model loaded AND Colab connected, instant switch  
✅ **Pre-configured Notebook** - Download ready-to-run Colab notebook from admin UI  
✅ **Automatic Setup** - Notebook installs all dependencies automatically  
✅ **Secure Connection** - Authentication token protects your Colab endpoint  

---

## Prerequisites

### Required
- ✅ **Google Account** (for Google Colab access)
- ✅ **VieNeu-TTS** running with admin access

### Required for Colab Connection
- ⭐ **ngrok Account** (free tier works) - **REQUIRED** for tunnel connection
  - Sign up at: https://ngrok.com/
  - Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken
  - Copy the full token (long alphanumeric string)

---

## Setup Guide

### Step 1: Configure Model in Admin UI

1. **Log in to Admin Dashboard** (`/admin` endpoint)
2. Navigate to **🔄 Backend Selection** section
3. Open **⚙️ Colab Configuration** accordion
4. Under **Step 1: Generate Notebook**, select:
   - **Backbone Model**: Choose model (e.g., VieNeu-TTS-q4-gguf for faster setup)
   - **Codec**: Choose codec (e.g., NeuCodec Standard)
   - **Device**: Auto (recommended) or CUDA/CPU
5. Click **📥 Download Colab Notebook**
6. **IMPORTANT**: Copy the **Auth Token** displayed (you'll need this later!)

### Step 2: Upload and Run Notebook in Google Colab

1. **Open Google Colab**
   - Go to: https://colab.research.google.com/
   - Sign in with your Google account

2. **Upload Notebook**
   - Click **File** → **Upload notebook**
   - Upload the `vieneu_tts_colab.ipynb` file you downloaded

3. **Select GPU Runtime** (Recommended)
   - Click **Runtime** → **Change runtime type**
   - Set **Hardware accelerator** to **GPU** (T4)
   - Click **Save**

4. **Configure ngrok Token (IMPORTANT!)**
   - Before running cells, find the cell with `NGROK_TOKEN = "YOUR_NGROK_TOKEN"`
   - Get your ngrok token:
     - Go to: https://dashboard.ngrok.com/get-started/your-authtoken
     - Copy your authtoken (should look like: `2abc...XYZ` - long alphanumeric)
   - Replace `"YOUR_NGROK_TOKEN"` with your actual token:
     ```python
     NGROK_TOKEN = "2abc...YourActualTokenHere...XYZ"
     ```
   - ⚠️ **Don't skip this!** Without a valid token, the connection will fail

5. **Run All Cells**
   - Click **Runtime** → **Run all**
   - Wait for installation (first run takes ~5-10 minutes)
   - Cells will:
     - ✅ Install espeak-ng
     - ✅ Install uv package manager
     - ✅ Clone VieNeu-TTS repository
     - ✅ Run `uv sync` to install all dependencies (more stable!)
     - ✅ Load the model
     - ✅ Start FastAPI server
     - ✅ Create ngrok tunnel (using your token)

6. **Copy Connection Details**
   - Scroll to the bottom of the last cell
   - You'll see output like:
     ```
     ════════════════════════════════════════════════
     🎉 VieNeu-TTS Colab Backend is READY!
     ════════════════════════════════════════════════
     
     📍 Endpoint URL: https://abc123-456.ngrok.io
     🔑 Auth Token: your-auth-token-here
     
     📋 Copy the above URL and Token to your Admin UI
     ```
   - **Copy both the Endpoint URL and Auth Token**

### Step 3: Connect from Admin UI

1. **Return to Admin Dashboard**
2. In **🔄 Backend Selection** → **⚙️ Colab Configuration**
3. Under **Step 3: Connect to Colab**:
   - Paste **Endpoint URL** (e.g., `https://abc123.ngrok.io`)
   - Paste **Auth Token** from Step 1 or from notebook output
4. Click **🔗 Connect**
5. Wait for confirmation: "✅ Connected successfully (latency: XXms)"

### Step 4: Switch Backend Mode

1. In **🔄 Backend Selection**, you'll see:
   - **💻 Local Backend** status (left column)
   - **☁️ Google Colab Backend** status (right column)

2. Select **Active Backend Mode**:
   - Choose **"Local"** to use your local machine
   - Choose **"Google Colab"** to use Colab backend

3. **Both backends can be ready!**
   - You can have local model loaded AND Colab connected
   - Switch instantly between them based on your needs

---

## Usage Tips

### When to Use Each Backend

| Scenario | Recommended Backend |
|----------|---------------------|
| You have powerful local GPU (RTX 3060+) | **Local** - Lower latency |
| Limited local resources (CPU only) | **Google Colab** - Free T4 GPU |
| Long TTS generation sessions | **Local** - No 12hr limit |
| Testing/development | **Either** - Switch freely! |
| Running on VPS without GPU | **Google Colab** - Offload to GPU |

### Performance Comparison

| Backend | Latency | GPU Memory | Cost | Time Limit |
|---------|---------|------------|------|------------|
| **Local (GPU)** | ~100-500ms | Varies | $$$ (electricity) | Unlimited |
| **Local (CPU)** | ~2-5s | N/A | $ | Unlimited |
| **Google Colab** | +100-500ms network | 15GB T4 | Free! | 12 hours |

### Monitoring Colab Status

- Use **🧪 Test Connection** button to check Colab health
- **💻 Local Backend** and **☁️ Google Colab Backend** panels show real-time status
- If Colab disconnects (12hr limit or idle timeout), you'll see "🔴 Disconnected"

---

## Troubleshooting

### Problem: "RuntimeError: Expected one of cpu, cuda, ... device type at start of device string: auto"

**Cause:**
- VieNeuTTS doesn't understand "auto" as a device string
- Needs explicit "cuda" or "cpu"

**Solution:**
**Option A: Download NEW notebook** (Recommended)
1. Go back to Admin UI
2. Click **Download Colab Notebook** again (I just fixed it to handle "auto" properly)
3. Upload the new notebook to Colab
4. Run all cells - it will auto-detect cuda/cpu

**Option B: Fix existing notebook manually**
1. Find the line: `DEVICE = "{{ device }}"`
2. Add these lines right after it:
```python
DEVICE = "auto"  # or whatever was generated

# Add these lines:
if DEVICE.lower() == "auto":
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Auto-detected device: {DEVICE}")
```
3. Re-run the FastAPI server cell

---

### Problem: "ModuleNotFoundError: No module named 'neucodec'" or "502 error responses"

**Cause:**
- VieNeu-TTS package and its dependencies (like `neucodec`) weren't installed
- The notebook only cloned the repo but didn't install it

**Solution:**
**Option A: Download NEW notebook** (Recommended)
1. Go back to Admin UI
2. Click **Download Colab Notebook** again (I fixed the template to install dependencies)
3. Upload the new notebook to Colab
4. Run all cells

**Option B: Fix existing notebook manually**
1. First, add a new cell BEFORE the git clone cell:
```python
# Install uv
!curl -LsSf https://astral.sh/uv/install.sh | sh
import os
os.environ['PATH'] = f"/root/.cargo/bin:{os.environ['PATH']}"
!uv --version
```

2. Then find the cell with `!git clone https://github.com/pnnbao-ump/Vina-TTS.git` and update it:
```python
!git clone https://github.com/pnnbao-ump/Vina-TTS.git
%cd Vina-TTS

# Use uv sync instead of pip
!uv sync
!uv pip install fastapi uvicorn pyngrok nest-asyncio
```

3. In the FastAPI server cell, add these lines at the very top:
```python
# Activate uv virtual environment
import sys
sys.path.insert(0, '/content/Vina-TTS/.venv/lib/python3.12/site-packages')

# Then the rest of the imports...
```

4. Re-run all the edited cells in order

---

### Problem: "RuntimeError: asyncio.run() cannot be called from a running event loop"

**Cause:**
- Colab runs in an existing asyncio event loop
- Old notebook version uses `uvicorn.run()` which tries to create a new loop

**Solution:**
**Option A: Download NEW notebook** (Recommended)
1. Go back to Admin UI
2. Click **Download Colab Notebook** again (I fixed the template)
3. Upload the new notebook to Colab
4. Delete the old notebook

**Option B: Fix the existing notebook manually**
1. In Colab, find the LAST cell with `uvicorn.run(app, host="0.0.0.0", port=8000)`
2. Replace that line with:
```python
# Start server (Colab-compatible)
import asyncio
from uvicorn import Config, Server

config = Config(app=app, host="0.0.0.0", port=8000, log_level="info")
server = Server(config)

# Run server in the existing event loop
await server.serve()
```
3. Re-run the cell

---

### Problem: "The authtoken you specified does not look like a proper ngrok authtoken"

**Possible Causes:**
- ngrok token not configured in notebook
- Wrong token copied (extra spaces, incomplete)
- Old/revoked token

**Solution:**
1. **Get fresh token from ngrok dashboard:**
   - Go to: https://dashboard.ngrok.com/get-started/your-authtoken
   - Copy the FULL token (should be ~50+ characters)

2. **In Colab notebook, edit the last cell:**
   - Find line: `NGROK_TOKEN = "YOUR_NGROK_TOKEN"`
   - Replace with: `NGROK_TOKEN = "2abc...your-actual-token...XYZ"`
   - Make sure no extra spaces or quotes

3. **Re-run just the last cell** (FastAPI + ngrok)
   - Don't need to restart whole notebook
   - Just click the play button on that cell again

4. **Verify token format:**
   - Should look like: `2abcDEF123xyz...` (alphanumeric, ~50-70 chars)
   - Should NOT have quotes inside the string
   - Should NOT have spaces at start/end

---

### Problem: "Connection test failed: Connection refused"

**Possible Causes:**
- Colab notebook stopped running
- ngrok tunnel expired
- Incorrect endpoint URL

**Solution:**
1. Check if Colab notebook cell is still running (look for spinning icon)
2. If cell stopped, re-run the last cell (FastAPI server + ngrok)
3. Copy the NEW endpoint URL (ngrok URL changes on restart)
4. Reconnect in Admin UI

---

### Problem: "Authentication token invalid"

**Possible Causes:**
- Wrong auth token entered
- Token from different notebook session

**Solution:**
1. Find the auth token in Colab notebook output (last cell)
2. Make sure you're copying the CURRENT token (matches current session)
3. In Admin UI, paste the correct token and click 🔗 Connect

---

### Problem: "Cannot switch to Colab: Not connected to Colab backend"

**Possible Causes:**
- Colab not connected yet
- Connection lost

**Solution:**
1. Check **☁️ Google Colab Backend** status - should show "🟢 Connected"
2. If "⚪ Not Connected", complete Step 3 (Connect to Colab)
3. If "🔴 Disconnected", click 🧪 Test Connection to diagnose

---

### Problem: "Colab runtime disconnected after 12 hours"

**Expected Behavior:**
- Google Colab free tier has 12-hour runtime limit
- Session will disconnect automatically

**Solution:**
1. In Colab, click **Runtime** → **Run all** to restart
2. Copy NEW endpoint URL and auth token
3. In Admin UI, click **🔌 Disconnect** then **🔗 Connect** with new details
4. OR: Just switch to **Local** backend temporarily

---

### Problem: "Model not loaded in Colab"

**Possible Causes:**
- Model download failed (network issue)
- Colab out of memory

**Solution:**
1. In Colab, check cell outputs for errors
2. Try using a smaller model (e.g., VieNeu-TTS-q4-gguf instead of full model)
3. Restart runtime: **Runtime** → **Restart and run all**

---

### Problem: "Cannot switch to Local: No local model loaded"

**Possible Causes:**
- Local model not loaded in **Model Control** panel

**Solution:**
1. Go to **🦜 Model Control** section in Admin UI
2. Select backbone, codec, and device
3. Click **📥 Load Model**
4. Wait for "✅ Model loaded successfully"
5. Now you can switch to **Local** backend mode

---

## Advanced Configuration

### Using Custom ngrok Domain

If you have a paid ngrok account with custom domains:

1. **Edit the Colab notebook** before running:
   ```python
   # Find this line in the last cell:
   ngrok.set_auth_token("YOUR_NGROK_TOKEN")
   
   # Replace with your actual ngrok token
   ngrok.set_auth_token("your_actual_ngrok_token_here")
   ```

2. **Connect with custom domain**:
   ```python
   # Change this line:
   public_url = ngrok.connect(8000)
   
   # To:
   public_url = ngrok.connect(8000, domain="your-domain.ngrok.app")
   ```

### Using cloudflared Instead of ngrok

If you prefer cloudflared (no account needed):

1. **Replace ngrok section** in Colab notebook with:
   ```python
   !wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
   !chmod +x cloudflared-linux-amd64
   
   import subprocess
   import threading
   
   def run_cloudflared():
       subprocess.run(["./cloudflared-linux-amd64", "tunnel", "--url", "http://localhost:8000"])
   
   tunnel_thread = threading.Thread(target=run_cloudflared, daemon=True)
   tunnel_thread.start()
   
   import time
   time.sleep(5)
   
   # Check tunnel logs for URL (appears in output)
   ```

2. Copy the cloudflared URL from output

### Environment Variable Configuration

Instead of saving to `config.yaml`, you can use environment variables:

```bash
export COLAB_ENDPOINT_URL="https://abc123.ngrok.io"
export COLAB_AUTH_TOKEN="your-token-here"
```

These will override config file values.

---

## FAQ

### Q: Can I use multiple Colab instances for load balancing?

**A:** Not currently. This feature only supports one Colab backend at a time. Future versions may add multi-instance support.

### Q: Does Colab backend support all voice samples?

**A:** Yes! All voice samples configured in your local `config.yaml` are sent to Colab for synthesis.

### Q: What happens to my data?

**A:** Text and voice sample references are sent to Colab via HTTPS. Audio is generated in Colab and returned. Nothing is permanently stored in Colab (session ends after 12hrs).

### Q: Can I use Kaggle instead of Colab?

**A:** Not directly supported yet, but the approach is similar. You'd need to manually adapt the notebook for Kaggle environment.

### Q: Will local users notice when I switch backends?

**A:** No! Backend switching is transparent to users. TTS requests are routed to the active backend automatically.

### Q: Do I need to restart the app to switch backends?

**A:** No! You can switch between Local and Colab backends anytime without restarting. This is a key feature of the hybrid design.

---

## Security Notes

🔒 **Keep your auth token secret!**
- The auth token protects your Colab endpoint from unauthorized access
- Don't share it publicly or commit it to git
- Tokens are unique per notebook session

🔒 **Use HTTPS endpoints only**
- ngrok provides HTTPS by default
- Never use plain HTTP for production

🔒 **Colab session isolation**
- Each Colab session is isolated
- Token expires when notebook stops
- No persistent storage between sessions

---

## Additional Resources

- **VieNeu-TTS Documentation**: [README.md](../README.md)
- **Google Colab Guide**: https://colab.research.google.com/
- **ngrok Documentation**: https://ngrok.com/docs
- **cloudflared Documentation**: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps

---

## Support

If you encounter issues not covered in this guide:

1. Check Admin UI status panels (💻 Local Backend / ☁️ Google Colab Backend)
2. Click 🧪 Test Connection to diagnose Colab issues
3. Review Colab notebook cell outputs for errors
4. Open an issue on GitHub with error details

Happy synthesizing! 🎉
