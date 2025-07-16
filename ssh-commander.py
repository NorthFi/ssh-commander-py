from flask import Flask, render_template, request

import paramiko
import subprocess
import platform

app = Flask(__name__)

ssh_connection = None

def check_ping(ip_address):
    try:
        ping_cmd = ["ping", "-n", "1"] if platform.system().lower() == "windows" else ["ping", "-c", "1"]
        subprocess.run(ping_cmd + [ip_address], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def establish_ssh_connection(remote_ip, username, password):
    global ssh_connection
    try:
        ssh_connection = paramiko.SSHClient()
        ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_connection.connect(remote_ip, username=username, password=password)
        return True
    except paramiko.AuthenticationException:
        return False
    except Exception as e:
        print(f"Error establishing SSH connection: {str(e)}")
        return False

def execute_ssh_script(script):
    global ssh_connection
    try:
        if ssh_connection is None or ssh_connection.get_transport() is None:
            return {'error': "SSH connection not established. Please check your connection details and try again."}

        stdin, stdout, stderr = ssh_connection.exec_command(script)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        return {
            'output': output,
            'error': error,
            'message': 'Script ran successfully' if not error else 'Script failed to run'
        }
    except Exception as e:
        return {'error': f"Error executing script: {str(e)}"}

def close_ssh_connection():
    global ssh_connection
    if ssh_connection is not None:
        ssh_connection.close()
        ssh_connection = None

@app.route('/')
def index():
    return render_template('index.html', result=None, is_connected=(ssh_connection is not None))

@app.route('/execute', methods=['POST'])
def execute():
    global ssh_connection
    remote_ip = request.form['remote_ip']
    username = request.form['username']
    password = request.form['password']
    user_script = request.form.get('script_input', '')

    if not ssh_connection or ssh_connection.get_transport() is None:
        if not establish_ssh_connection(remote_ip, username, password):
            return render_template('index.html', result={'error': 'Unable to establish SSH connection. Check your credentials and try again.'}, is_connected=False)

    result = execute_ssh_script(user_script)

    return render_template('index.html', result=result, is_connected=(ssh_connection is not None))

@app.route('/execute_additional', methods=['POST'])
def execute_additional():
    global ssh_connection
    additional_script = request.form.get('additional_script', '')

    if not ssh_connection or ssh_connection.get_transport() is None:
        return render_template('index.html', result={'error': 'SSH connection not established. Please log in to execute additional scripts.'}, is_connected=False)

    result = execute_ssh_script(additional_script)

    return render_template('index.html', result=result, is_connected=(ssh_connection is not None))

@app.route('/end_session', methods=['POST'])
def end_session():
    global ssh_connection
    close_ssh_connection()
    return render_template('index.html', result={'message': 'SSH session ended successfully.'}, is_connected=False)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
