import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('BEGET_HOST')
USER = os.getenv('BEGET_USER')
PASS = os.getenv('BEGET_PASSWORD')
REMOTE_PATH = os.getenv('BEGET_REMOTE_PATH')
LOCAL_FILE = 'static_dashboard.html'

def deploy():
    print(f"🚀 Deploying Full Dashboard to {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, password=PASS)
        print("✅ SSH Connected")
        
        # Create directory
        print(f"📂 Creating remote directory: {REMOTE_PATH}")
        ssh.exec_command(f"mkdir -p {REMOTE_PATH}")
        
        # SFTP Upload
        sftp = ssh.open_sftp()
        remote_file = f"{REMOTE_PATH}/index.html"
        print(f"📤 Uploading {LOCAL_FILE} -> {remote_file}")
        sftp.put(LOCAL_FILE, remote_file)
        
        print("✅ Upload Complete!")
        print("🌍 URL: http://dev.5na5.ru/project/signalizer/")
        sftp.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()
