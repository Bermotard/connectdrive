with open('src/services/mount_service.py', 'r') as f:
    content = f.read()

# Normalize line endings to \n
with open('src/services/mount_service.py', 'w', newline='\n') as f:
    f.write(content)
