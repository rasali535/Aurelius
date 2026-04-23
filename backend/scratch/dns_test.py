import socket
host = "aws-0-eu-west-1.pooler.supabase.com"
try:
    print(f"Resolving {host}...")
    info = socket.getaddrinfo(host, 6543)
    print(f"Resolved: {info}")
except Exception as e:
    print(f"Failed: {e}")
