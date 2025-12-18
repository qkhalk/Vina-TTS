import gradio as gr
import yaml
import os
import json
import secrets
from model_manager import ModelManager, ModelStatus, BackendMode
from auth import verify_admin_password, UserManager, SessionManager, UserRole
from colab.notebook_generator import NotebookGenerator


# Load configuration
CONFIG_PATH = "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f) or {}

BACKBONE_CONFIGS = _config.get("backbone_configs", {})
CODEC_CONFIGS = _config.get("codec_configs", {})

# Initialize managers
model_manager = ModelManager.get_instance()
user_manager = UserManager()
session_manager = SessionManager()


def admin_login(password: str):
    """Handle admin login."""
    try:
        if verify_admin_password(password):
            token = session_manager.create_session("admin", UserRole.ADMIN)
            return (
                gr.update(visible=False),  # Hide login
                gr.update(visible=True),   # Show dashboard
                token,
                "✅ Login successful"
            )
        else:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                "",
                "❌ Invalid password"
            )
    except Exception as e:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            "",
            f"❌ Error: {str(e)}"
        )


def validate_admin_session(token: str):
    """Validate admin session token."""
    if not token:
        return False
    session = session_manager.validate_session(token)
    return session is not None and session["role"] == UserRole.ADMIN


def load_model_action(token, backbone, codec, device, enable_triton, max_batch_size):
    """Admin action: Load model."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    backbone_config = BACKBONE_CONFIGS.get(backbone, {})
    codec_config = CODEC_CONFIGS.get(codec, {})
    
    if not backbone_config or not codec_config:
        return "❌ Invalid configuration", gr.update()
    
    # Determine codec device
    codec_device = "cpu" if "ONNX" in codec else device
    
    result = model_manager.load_model(
        backbone_repo=backbone_config["repo"],
        codec_repo=codec_config["repo"],
        backbone_device=device,
        codec_device=codec_device,
        enable_triton=enable_triton,
        max_batch_size=max_batch_size,
    )
    
    status = result["status"]
    message = result["message"]
    
    if result["success"]:
        status_text = f"✅ {message}\n\n" + format_status(status)
    else:
        status_text = f"❌ {message}\n\n" + format_status(status)
    
    return status_text, gr.update(value=format_status(model_manager.get_status()))


def unload_model_action(token):
    """Admin action: Unload model."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    result = model_manager.unload_model()
    message = result["message"]
    
    if result["success"]:
        status_text = f"✅ {message}"
    else:
        status_text = f"❌ {message}"
    
    return status_text, gr.update(value=format_status(model_manager.get_status()))


def restart_model_action(token):
    """Admin action: Restart model."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    result = model_manager.restart_model()
    message = result["message"]
    
    if result["success"]:
        status_text = f"✅ {message}"
    else:
        status_text = f"❌ {message}"
    
    return status_text, gr.update(value=format_status(model_manager.get_status()))


def format_status(status_info):
    """Format status dict for display."""
    lines = [
        f"**Status:** {status_info['status'].upper()}",
        f"**Backend:** {status_info['backend']}",
    ]
    
    if status_info.get('error'):
        lines.append(f"**Error:** {status_info['error']}")
    
    config = status_info.get('config', {})
    if config:
        lines.append(f"**Backbone:** {config.get('backbone_repo', 'N/A')}")
        lines.append(f"**Codec:** {config.get('codec_repo', 'N/A')}")
        lines.append(f"**Device:** {config.get('backbone_device', 'N/A')}")
    
    if 'gpu_memory_allocated' in status_info:
        lines.append(f"**GPU Memory:** {status_info['gpu_memory_allocated']:.2f} GB / {status_info['gpu_memory_reserved']:.2f} GB")
    
    return "\n".join(lines)


def get_users_list(token):
    """Get formatted list of users."""
    if not validate_admin_session(token):
        return "❌ Unauthorized"
    
    users = user_manager.get_all_users()
    if not users:
        return "No users registered"
    
    lines = ["| Username | Status | Created Date | Actions |",
             "|----------|--------|--------------|---------|"]
    for user in users:
        status = "✅ Enabled" if user.enabled else "❌ Disabled"
        lines.append(f"| {user.username} | {status} | {user.created_at} | - |")
    
    return "\n".join(lines)


def get_users_list_for_dropdown(token):
    """Get list of usernames for dropdown."""
    if not validate_admin_session(token):
        return []
    
    users = user_manager.get_all_users()
    return [user.username for user in users]


def add_user_action(token, username, password):
    """Admin action: Add user."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update(), gr.update()
    
    if not username or not password:
        return "❌ Username and password required", gr.update(), gr.update()
    
    if len(password) < 8:
        return "❌ Password must be at least 8 characters", gr.update(), gr.update()
    
    success = user_manager.add_user(username, password)
    
    if success:
        users_list = get_users_list(token)
        users_dropdown = get_users_list_for_dropdown(token)
        return f"✅ User '{username}' added successfully", gr.update(value=users_list), gr.update(choices=users_dropdown)
    else:
        return f"❌ Username '{username}' already exists", gr.update(), gr.update()


def remove_user_action(token, username):
    """Admin action: Remove user."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update(), gr.update()
    
    if not username:
        return "❌ Username required", gr.update(), gr.update()
    
    success = user_manager.remove_user(username)
    session_manager.invalidate_user_sessions(username)
    
    if success:
        users_list = get_users_list(token)
        users_dropdown = get_users_list_for_dropdown(token)
        return f"✅ User '{username}' removed successfully", gr.update(value=users_list), gr.update(choices=users_dropdown, value=None)
    else:
        return f"❌ User '{username}' not found", gr.update(), gr.update()


def enable_user_action(token, username):
    """Admin action: Enable user."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    if not username:
        return "❌ Please select a user", gr.update()
    
    success = user_manager.set_user_enabled(username, True)
    
    if success:
        users_list = get_users_list(token)
        return f"✅ User '{username}' enabled", gr.update(value=users_list)
    else:
        return f"❌ User '{username}' not found", gr.update()


def disable_user_action(token, username):
    """Admin action: Disable user."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    if not username:
        return "❌ Please select a user", gr.update()
    
    success = user_manager.set_user_enabled(username, False)
    
    if success:
        session_manager.invalidate_user_sessions(username)
        users_list = get_users_list(token)
        return f"✅ User '{username}' disabled", gr.update(value=users_list)
    else:
        return f"❌ User '{username}' not found", gr.update()


def refresh_user_data(token):
    """Refresh user list and dropdown."""
    return get_users_list(token), gr.update(choices=get_users_list_for_dropdown(token))


def switch_backend_mode_action(token, mode):
    """Admin action: Switch backend mode."""
    if not validate_admin_session(token):
        return "❌ Unauthorized"
    
    try:
        # Validate mode is available
        if mode == "Google Colab" and not model_manager._colab_connected:
            return "❌ Cannot switch to Colab: Not connected to Colab backend"
        
        if mode == "Local" and model_manager.status != ModelStatus.LOADED:
            return "❌ Cannot switch to Local: No local model loaded"
        
        # Switch mode
        new_mode = BackendMode.REMOTE if mode == "Google Colab" else BackendMode.LOCAL
        model_manager.backend_mode = new_mode
        
        return f"✅ Switched to {mode} backend"
        
    except Exception as e:
        return f"❌ Error switching backend: {str(e)}"


def generate_notebook_action(token, backbone, codec, device):
    """Admin action: Generate and download Colab notebook."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", None
    
    try:
        backbone_config = BACKBONE_CONFIGS.get(backbone, {})
        codec_config = CODEC_CONFIGS.get(codec, {})
        
        if not backbone_config or not codec_config:
            return "❌ Invalid model configuration", None
        
        # Generate notebook
        generator = NotebookGenerator()
        notebook_json, auth_token = generator.generate(
            backbone_repo=backbone_config["repo"],
            codec_repo=codec_config["repo"],
            device=device.lower()
        )
        
        # Save to temp file for download
        temp_path = "vieneu_tts_colab.ipynb"
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(notebook_json)
        
        message = f"✅ Notebook generated!\\n\\n🔑 **Auth Token:** `{auth_token}`\\n\\n📥 Download the notebook and run it in Google Colab."
        
        return message, temp_path
        
    except Exception as e:
        return f"❌ Error generating notebook: {str(e)}", None


def connect_colab_action(token, endpoint_url, auth_token):
    """Admin action: Connect to Colab backend."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    if not endpoint_url or not auth_token:
        return "❌ Please provide both endpoint URL and auth token", gr.update()
    
    result = model_manager.set_colab_connection(endpoint_url.strip(), auth_token.strip())
    
    if result["success"]:
        status = f"✅ {result['message']}"
    else:
        status = f"❌ {result['message']}"
    
    # Return status and updated connection display
    return status, gr.update(value=format_colab_status())


def disconnect_colab_action(token):
    """Admin action: Disconnect from Colab backend."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    result = model_manager.disconnect_colab()
    
    if result["success"]:
        status = f"✅ {result['message']}"
    else:
        status = f"❌ {result['message']}"
    
    return status, gr.update(value=format_colab_status())


def test_colab_connection_action(token):
    """Admin action: Test Colab connection."""
    if not validate_admin_session(token):
        return "❌ Unauthorized"
    
    health = model_manager.check_colab_health()
    
    if health.get("connected"):
        health_data = health.get("health", {})
        gpu_mem = health_data.get("gpu_memory_used_gb", 0)
        model_loaded = health_data.get("model_loaded", False)
        
        return f"✅ Connection OK\\n\\n**Model Loaded:** {'Yes' if model_loaded else 'No'}\\n**GPU Memory:** {gpu_mem:.2f} GB"
    else:
        return f"❌ {health.get('message', 'Connection failed')}"


def format_colab_status():
    """Format Colab connection status for display."""
    if model_manager._colab_connected:
        health = model_manager.check_colab_health()
        if health.get("connected"):
            health_data = health.get("health", {})
            lines = [
                "**Status:** 🟢 Connected",
                f"**Endpoint:** {model_manager._colab_endpoint}",
                f"**Model Loaded:** {'Yes' if health_data.get('model_loaded') else 'No'}",
            ]
            if health_data.get("gpu_available"):
                lines.append(f"**GPU Memory:** {health_data.get('gpu_memory_used_gb', 0):.2f} GB")
            return "\\n".join(lines)
        else:
            return f"**Status:** 🔴 Disconnected\\n{health.get('message', '')}"
    else:
        return "**Status:** ⚪ Not Connected"


def toggle_access_protection(token, enabled):
    """Admin action: Toggle user access protection."""
    if not validate_admin_session(token):
        return "❌ Unauthorized"
    
    user_manager.set_access_enabled(enabled)
    status = "enabled" if enabled else "disabled"
    return f"✅ User access protection {status}"


def refresh_model_status(token):
    """Refresh model status display."""
    if not validate_admin_session(token):
        return "❌ Unauthorized"
    
    return format_status(model_manager.get_status())


def recover_admin_session():
    """Recover admin session from localStorage on page load."""
    return """
    function() {
        const token = localStorage.getItem('vieneu_admin_session') || '';
        console.log('Recovering admin session:', token ? 'Token found' : 'No token');
        return token;
    }
    """


def admin_logout(token):
    """Handle admin logout."""
    if token:
        session_manager.invalidate_session(token)
    return (
        gr.update(visible=True),   # Show login
        gr.update(visible=False),  # Hide dashboard
        "",                        # Clear token
        "Logged out successfully"
    )


def validate_and_restore_admin_session(token):
    """Validate token and restore dashboard state."""
    if not token or not validate_admin_session(token):
        # Invalid session - show login
        return (
            gr.update(visible=True),   # Show login
            gr.update(visible=False),  # Hide dashboard
            "",                        # Clear token
            "",                        # Clear login status
            format_status(model_manager.get_status()),  # Model status
            user_manager.is_access_enabled(),           # Access protection
            get_users_list(token) if token else "No users"  # User list
        )
    else:
        # Valid session - show dashboard
        return (
            gr.update(visible=False),  # Hide login
            gr.update(visible=True),   # Show dashboard
            token,                     # Keep token
            "",                        # Clear login status
            format_status(model_manager.get_status()),  # Model status
            user_manager.is_access_enabled(),           # Access protection
            get_users_list(token)      # User list
        )


def create_admin_interface():
    """Create admin Gradio interface."""
    
    with gr.Blocks(title="VieNeu-TTS Admin", js=recover_admin_session()) as admin_interface:
        session_token = gr.State("")
        
        # Login page
        with gr.Column(visible=True) as login_page:
            gr.Markdown("# 🔐 Admin Login")
            admin_password = gr.Textbox(
                label="Admin Password",
                type="password",
                placeholder="Enter admin password"
            )
            login_btn = gr.Button("Login", variant="primary")
            login_status = gr.Markdown("")
        
        # Dashboard
        with gr.Column(visible=False) as dashboard_page:
            gr.Markdown("# ⚙️ VieNeu-TTS Admin Dashboard")
            
            # Model Control Panel
            with gr.Group():
                gr.Markdown("## 🦜 Model Control")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        backbone_select = gr.Dropdown(
                            choices=list(BACKBONE_CONFIGS.keys()),
                            value=list(BACKBONE_CONFIGS.keys())[0] if BACKBONE_CONFIGS else None,
                            label="Backbone Model"
                        )
                        codec_select = gr.Dropdown(
                            choices=list(CODEC_CONFIGS.keys()),
                            value=list(CODEC_CONFIGS.keys())[0] if CODEC_CONFIGS else None,
                            label="Codec"
                        )
                        device_select = gr.Radio(
                            choices=["Auto", "CPU", "CUDA"],
                            value="Auto",
                            label="Device"
                        )
                        
                        with gr.Row():
                            enable_triton_check = gr.Checkbox(
                                value=True,
                                label="Enable Triton"
                            )
                            max_batch_slider = gr.Slider(
                                minimum=1,
                                maximum=16,
                                value=8,
                                step=1,
                                label="Max Batch Size"
                            )
                    
                    with gr.Column(scale=1):
                        model_status_display = gr.Markdown(
                            format_status(model_manager.get_status())
                        )
                        refresh_status_btn = gr.Button("🔄 Refresh Status")
                
                with gr.Row():
                    load_model_btn = gr.Button("📥 Load Model", variant="primary")
                    unload_model_btn = gr.Button("📤 Unload Model")
                    restart_model_btn = gr.Button("🔄 Restart Model")
                
                model_action_status = gr.Markdown("")
            
            # Backend Selection Panel
            with gr.Group():
                gr.Markdown("## 🔄 Backend Selection")
                gr.Markdown("*Choose where TTS processing happens: Local machine or Google Colab*")
                
                # Backend mode selector
                backend_mode_radio = gr.Radio(
                    choices=["Local", "Google Colab"],
                    value="Local",
                    label="Active Backend Mode",
                    info="Select which backend to use for TTS synthesis"
                )
                backend_switch_status = gr.Markdown("")
                
                with gr.Row():
                    # Local Backend Status
                    with gr.Column(scale=1):
                        gr.Markdown("### 💻 Local Backend")
                        local_backend_status = gr.Markdown(
                            format_status(model_manager.get_status())
                        )
                    
                    # Colab Backend Status
                    with gr.Column(scale=1):
                        gr.Markdown("### ☁️ Google Colab Backend")
                        colab_backend_status = gr.Markdown(format_colab_status())
                
                # Colab Configuration
                with gr.Accordion("⚙️ Colab Configuration", open=False):
                    gr.Markdown("### Step 1: Generate Notebook")
                    gr.Markdown("Configure model settings and download a pre-configured Colab notebook.")
                    
                    with gr.Row():
                        notebook_backbone = gr.Dropdown(
                            choices=list(BACKBONE_CONFIGS.keys()),
                            value=list(BACKBONE_CONFIGS.keys())[0] if BACKBONE_CONFIGS else None,
                            label="Backbone Model",
                            scale=2
                        )
                        notebook_codec = gr.Dropdown(
                            choices=list(CODEC_CONFIGS.keys()),
                            value=list(CODEC_CONFIGS.keys())[0] if CODEC_CONFIGS else None,
                            label="Codec",
                            scale=2
                        )
                        notebook_device = gr.Radio(
                            choices=["Auto", "CUDA", "CPU"],
                            value="Auto",
                            label="Device",
                            scale=1
                        )
                    
                    generate_notebook_btn = gr.Button("📥 Download Colab Notebook", variant="primary")
                    notebook_file = gr.File(label="Generated Notebook", visible=True)
                    notebook_status = gr.Markdown("")
                    
                    gr.Markdown("### Step 2: Run in Colab")
                    gr.Markdown("1. Upload the downloaded notebook to [Google Colab](https://colab.research.google.com/)\\n"
                               "2. Run all cells in the notebook\\n"
                               "3. Copy the **Endpoint URL** and **Auth Token** displayed at the end")
                    
                    gr.Markdown("### Step 3: Connect to Colab")
                    
                    colab_endpoint_url = gr.Textbox(
                        label="Endpoint URL",
                        placeholder="https://abc123.ngrok.io",
                        info="Copy from Colab notebook output"
                    )
                    colab_auth_token = gr.Textbox(
                        label="Auth Token",
                        type="password",
                        placeholder="Enter the auth token from notebook",
                        info="Keep this secret!"
                    )
                    
                    with gr.Row():
                        connect_colab_btn = gr.Button("🔗 Connect", variant="primary")
                        disconnect_colab_btn = gr.Button("🔌 Disconnect")
                        test_colab_btn = gr.Button("🧪 Test Connection")
                    
                    colab_action_status = gr.Markdown("")
            
            # User Management Panel
            with gr.Group():
                gr.Markdown("## 👥 User Management")
                
                access_protection_check = gr.Checkbox(
                    value=user_manager.is_access_enabled(),
                    label="Enable User Access Protection (require login for users)"
                )
                access_protection_status = gr.Markdown("")
                
                # Add User Section
                with gr.Group():
                    gr.Markdown("### ➕ Add New User")
                    with gr.Row():
                        new_username = gr.Textbox(label="Username", placeholder="username", scale=2)
                        new_password = gr.Textbox(label="Password", type="password", placeholder="min 8 characters", scale=2)
                        add_user_btn = gr.Button("Add User", variant="primary", scale=1)
                    add_user_status = gr.Markdown("")
                
                # User List and Actions
                gr.Markdown("### 📋 Registered Users")
                users_list_display = gr.Markdown(get_users_list(session_token.value))
                
                with gr.Row():
                    user_select = gr.Dropdown(
                        label="Select User",
                        choices=get_users_list_for_dropdown(session_token.value),
                        scale=2
                    )
                    refresh_users_btn = gr.Button("🔄 Refresh", scale=1)
                
                # User Actions
                with gr.Row():
                    with gr.Column():
                        enable_user_btn = gr.Button("✅ Enable User", variant="primary")
                        enable_user_status = gr.Markdown("")
                    
                    with gr.Column():
                        disable_user_btn = gr.Button("🚫 Disable User", variant="secondary")
                        disable_user_status = gr.Markdown("")
                    
                    with gr.Column():
                        remove_user_btn = gr.Button("🗑️ Remove User", variant="stop")
                        remove_user_status = gr.Markdown("")
        
        # JavaScript to store token in localStorage
        store_token_js = """
        function(login_visible, dashboard_visible, token, status) {
            if (token) {
                localStorage.setItem('vieneu_admin_session', token);
                console.log('Admin token stored in localStorage');
            }
            return [login_visible, dashboard_visible, token, status];
        }
        """
        
        # JavaScript to clear token from localStorage
        clear_token_js = """
        function(login_visible, dashboard_visible, token, status) {
            localStorage.removeItem('vieneu_admin_session');
            console.log('Admin token cleared from localStorage');
            return [login_visible, dashboard_visible, token, status];
        }
        """
        
        # Event handlers
        login_btn.click(
            fn=admin_login,
            inputs=[admin_password],
            outputs=[login_page, dashboard_page, session_token, login_status],
            js=store_token_js
        )
        
        # Add logout button handler (if logout button exists)
        # Note: We'll add explicit logout button in the dashboard
        
        # Load event to restore session
        admin_interface.load(
            fn=validate_and_restore_admin_session,
            inputs=[session_token],
            outputs=[
                login_page,
                dashboard_page,
                session_token,
                login_status,
                model_status_display,
                access_protection_check,
                users_list_display
            ]
        )
        
        load_model_btn.click(
            fn=load_model_action,
            inputs=[session_token, backbone_select, codec_select, device_select, enable_triton_check, max_batch_slider],
            outputs=[model_action_status, model_status_display]
        )
        
        unload_model_btn.click(
            fn=unload_model_action,
            inputs=[session_token],
            outputs=[model_action_status, model_status_display]
        )
        
        restart_model_btn.click(
            fn=restart_model_action,
            inputs=[session_token],
            outputs=[model_action_status, model_status_display]
        )
        
        refresh_status_btn.click(
            fn=refresh_model_status,
            inputs=[session_token],
            outputs=[model_status_display]
        )
        
        access_protection_check.change(
            fn=toggle_access_protection,
            inputs=[session_token, access_protection_check],
            outputs=[access_protection_status]
        )
        
        add_user_btn.click(
            fn=add_user_action,
            inputs=[session_token, new_username, new_password],
            outputs=[add_user_status, users_list_display, user_select]
        )
        
        enable_user_btn.click(
            fn=enable_user_action,
            inputs=[session_token, user_select],
            outputs=[enable_user_status, users_list_display]
        )
        
        disable_user_btn.click(
            fn=disable_user_action,
            inputs=[session_token, user_select],
            outputs=[disable_user_status, users_list_display]
        )
        
        remove_user_btn.click(
            fn=remove_user_action,
            inputs=[session_token, user_select],
            outputs=[remove_user_status, users_list_display, user_select]
        )
        
        refresh_users_btn.click(
            fn=refresh_user_data,
            inputs=[session_token],
            outputs=[users_list_display, user_select]
        )
        
        # Backend Selection event handlers
        backend_mode_radio.change(
            fn=switch_backend_mode_action,
            inputs=[session_token, backend_mode_radio],
            outputs=[backend_switch_status]
        )
        
        generate_notebook_btn.click(
            fn=generate_notebook_action,
            inputs=[session_token, notebook_backbone, notebook_codec, notebook_device],
            outputs=[notebook_status, notebook_file]
        )
        
        connect_colab_btn.click(
            fn=connect_colab_action,
            inputs=[session_token, colab_endpoint_url, colab_auth_token],
            outputs=[colab_action_status, colab_backend_status]
        )
        
        disconnect_colab_btn.click(
            fn=disconnect_colab_action,
            inputs=[session_token],
            outputs=[colab_action_status, colab_backend_status]
        )
        
        test_colab_btn.click(
            fn=test_colab_connection_action,
            inputs=[session_token],
            outputs=[colab_action_status]
        )
    
    return admin_interface
