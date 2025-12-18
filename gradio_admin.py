import gradio as gr
import yaml
import os
from model_manager import ModelManager, ModelStatus
from auth import verify_admin_password, UserManager, SessionManager, UserRole


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
    
    lines = []
    for user in users:
        status = "✅ Enabled" if user.enabled else "❌ Disabled"
        lines.append(f"• **{user.username}** - {status} (Created: {user.created_at})")
    
    return "\n".join(lines)


def add_user_action(token, username, password):
    """Admin action: Add user."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    if not username or not password:
        return "❌ Username and password required", gr.update()
    
    if len(password) < 8:
        return "❌ Password must be at least 8 characters", gr.update()
    
    success = user_manager.add_user(username, password)
    
    if success:
        users_list = get_users_list(token)
        return f"✅ User '{username}' added successfully", gr.update(value=users_list)
    else:
        return f"❌ Username '{username}' already exists", gr.update()


def remove_user_action(token, username):
    """Admin action: Remove user."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    if not username:
        return "❌ Username required", gr.update()
    
    success = user_manager.remove_user(username)
    session_manager.invalidate_user_sessions(username)
    
    if success:
        users_list = get_users_list(token)
        return f"✅ User '{username}' removed successfully", gr.update(value=users_list)
    else:
        return f"❌ User '{username}' not found", gr.update()


def toggle_user_enabled_action(token, username, enabled):
    """Admin action: Enable/disable user."""
    if not validate_admin_session(token):
        return "❌ Unauthorized", gr.update()
    
    if not username:
        return "❌ Username required", gr.update()
    
    success = user_manager.set_user_enabled(username, enabled)
    
    if success:
        if not enabled:
            session_manager.invalidate_user_sessions(username)
        users_list = get_users_list(token)
        status_text = "enabled" if enabled else "disabled"
        return f"✅ User '{username}' {status_text}", gr.update(value=users_list)
    else:
        return f"❌ User '{username}' not found", gr.update()


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


def create_admin_interface():
    """Create admin Gradio interface."""
    
    with gr.Blocks(title="VieNeu-TTS Admin") as admin_interface:
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
            
            # User Management Panel
            with gr.Group():
                gr.Markdown("## 👥 User Management")
                
                access_protection_check = gr.Checkbox(
                    value=user_manager.is_access_enabled(),
                    label="Enable User Access Protection (require login for users)"
                )
                access_protection_status = gr.Markdown("")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Add User")
                        new_username = gr.Textbox(label="Username", placeholder="username")
                        new_password = gr.Textbox(label="Password", type="password", placeholder="min 8 characters")
                        add_user_btn = gr.Button("➕ Add User", variant="primary")
                        add_user_status = gr.Markdown("")
                    
                    with gr.Column():
                        gr.Markdown("### Remove User")
                        remove_username = gr.Textbox(label="Username", placeholder="username")
                        remove_user_btn = gr.Button("➖ Remove User", variant="stop")
                        remove_user_status = gr.Markdown("")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Enable/Disable User")
                        toggle_username = gr.Textbox(label="Username", placeholder="username")
                        toggle_enabled = gr.Checkbox(label="Enabled", value=True)
                        toggle_user_btn = gr.Button("🔄 Update Status")
                        toggle_user_status = gr.Markdown("")
                
                gr.Markdown("### Current Users")
                users_list_display = gr.Markdown(get_users_list(session_token.value))
                refresh_users_btn = gr.Button("🔄 Refresh Users")
        
        # Event handlers
        login_btn.click(
            fn=admin_login,
            inputs=[admin_password],
            outputs=[login_page, dashboard_page, session_token, login_status]
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
            outputs=[add_user_status, users_list_display]
        )
        
        remove_user_btn.click(
            fn=remove_user_action,
            inputs=[session_token, remove_username],
            outputs=[remove_user_status, users_list_display]
        )
        
        toggle_user_btn.click(
            fn=toggle_user_enabled_action,
            inputs=[session_token, toggle_username, toggle_enabled],
            outputs=[toggle_user_status, users_list_display]
        )
        
        refresh_users_btn.click(
            fn=lambda token: get_users_list(token),
            inputs=[session_token],
            outputs=[users_list_display]
        )
    
    return admin_interface
