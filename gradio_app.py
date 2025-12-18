import gradio as gr
import os
from dotenv import load_dotenv
from auth import require_admin_password
from gradio_admin import create_admin_interface
from gradio_user import create_user_interface

# Load environment variables from .env file
load_dotenv()

print("⏳ Starting VieNeu-TTS...")

# Validate admin password is set
try:
    require_admin_password()
except ValueError as e:
    print(f"\n❌ Configuration Error: {e}\n")
    print("💡 Make sure you have a .env file with ADMIN_PASSWORD set")
    print("   Example: cp .env.example .env && edit .env\n")
    exit(1)

# Create interfaces
print("📦 Creating admin interface...")
admin_interface = create_admin_interface()

print("📦 Creating user interface...")
user_interface = create_user_interface()

# Mount both interfaces in tabs
demo = gr.TabbedInterface(
    [user_interface, admin_interface],
    ["🦜 TTS Service", "⚙️ Admin Panel"],
    title="VieNeu-TTS",
    theme=gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="cyan",
        neutral_hue="slate",
    )
)

if __name__ == "__main__":
    # Override from environment (useful for Docker)
    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    
    print(f"\n✅ VieNeu-TTS is ready!")
    print(f"   User Interface: http://{server_name}:{server_port}")
    print(f"   Admin Panel: Click 'Admin Panel' tab\n")
    
    demo.queue().launch(
        server_name=server_name,
        server_port=server_port,
        show_error=True
    )
