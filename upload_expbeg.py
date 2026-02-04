import paramiko
import os

HOST = 'ttimbah0.beget.tech'
USER = 'ttimbah0'
PASS = '@@Ae32c1c5'
REMOTE_PATH = '/home/t/ttimbah0/dev.5na5.ru/public_html/project/expbeg'
LOCAL_FILE = 'expbeg_index.html'

def deploy():
    print(f"🚀 Deploying to {HOST}...")
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
        print("🌍 URL: http://dev.5na5.ru/project/expbeg/")
        sftp.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()
