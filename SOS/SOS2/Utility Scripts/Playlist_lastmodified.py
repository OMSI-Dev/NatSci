import subprocess

command = 'ssh sos@10.10.51.98 "stat -c %y /home/sos/sosrc/normal-demo.sos"'

try:
    # Captures the output of the command
    result = subprocess.check_output(command, shell=True, text=True)
    # Parse the date from the output (format: "2026-01-13 12:34:56.123456789 -0800")
    modification_date = result.strip().split()[0]
    print(f"Modification Date: {modification_date}")
except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e}")