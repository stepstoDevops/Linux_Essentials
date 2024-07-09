import smtplib
import psutil
import os
import datetime
#import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Function to get system status information
def get_system_status():
    #boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Format system status as HTML
    status = (
        "<html>"
        "<body>"
        "    <h2>System Status Report</h2>"
        "    <p><strong>CPU Usage:</strong> {}%</p>"
        "    <p><strong>Memory Usage:</strong> {}% ({})</p>"
        "    <p><strong>Disk Usage:</strong> {}% ({})</p>"
        "</body>"
        "</html>"
    ).format(

        cpu_usage,
        memory.percent, convert_bytes(memory.used), convert_bytes(memory.total),
        disk.percent, convert_bytes(disk.used), convert_bytes(disk.total)
    )
    return status

# Function to convert bytes to a more human-readable format
def convert_bytes(bytes):
    """
    Convert bytes to a more human-readable format.
    """
    if bytes == 0:
        return "0 B"
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while bytes >= 1024 and i < len(suffixes)-1:
        bytes /= 1024.
        i += 1
    f = ('%.2f' % bytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

# Function to retrieve secret from AWS Secrets Manager
def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {str(e)}")
        return None
    else:
        if 'SecretString' in response:
            secret = response['SecretString']
            return secret
        else:
            print(f"No secret string found in response for {secret_name}")
            return None

# Function to write system status to HTML file
def write_system_status_to_file(file_path):
    system_status = get_system_status()
    with open(file_path, 'w') as f:
        f.write(system_status)

# Function to send email
def send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path=None):
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    # Attach body of email (HTML content)
    message.attach(MIMEText(body, 'html'))

    # Attach file if provided
    if attachment_path:
        filename = os.path.basename(attachment_path)
        attachment = open(attachment_path, "rb")

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename= {}'.format(filename))

        message.attach(part)

    # Connect to Gmail's SMTP server
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())

if __name__ == "__main__":
    # Gmail sender credentials
    sender_email = "stepstodevops@gmail.com"
    secret_name = os.getenv('GmailToken')  # Name of your secret in AWS Secrets Manager - "MyGmailPassword"

    # Retrieve Gmail password from AWS Secrets Manager
    sender_password = secret_name    # get_secret(secret_name) when want to retrive from aws
    if not sender_password:
        exit(1)  # Exit if password retrieval fails

    # Receiver email
    receiver_email = "stepstodevops@gmail.com"

    # Email subject
    subject = "System Status Report"

    # Generate HTML content for email body
    body = get_system_status()

    # File to attach (system status file)
    attachment_path = "/home/vagrant/system_status.html"  # Replace with actual path

    # Write system status to HTML file
    write_system_status_to_file(attachment_path)

    # Send email
    send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path)