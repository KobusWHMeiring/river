import os
import secrets
import string

def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("--- Django Server Config Generator ---")
    
    # Inputs
    app_name = input("App Name (e.g., market): ").strip().lower()
    domain = input("Domain (e.g., market.plot.org.za): ").strip().lower()
    proj_folder = input("Project Folder (where settings.py is): ").strip()
    has_celery = input("Enable Celery? (y/n): ").lower() == 'y'
    redis_db = input("Redis DB Number (0=Legacy, 1=Market, use 2+): ").strip()

    # Derived Variables
    base_path = f"/home/carbonplanner/apps/{app_name}"
    db_pass = generate_password()
    secret_key = generate_password(50)

    # Create local directory
    if not os.path.exists(app_name):
        os.makedirs(app_name)

    # 1. PSQL COMMANDS
    psql_content = f"""-- 1. Create DB and User
CREATE DATABASE {app_name}_db;
CREATE USER {app_name}_user WITH PASSWORD '{db_pass}';
GRANT ALL PRIVILEGES ON DATABASE {app_name}_db TO {app_name}_user;

-- 2. Move INTO the new database (CRITICAL)
\\c {app_name}_db

-- 3. Grant the internal permissions
GRANT ALL ON SCHEMA public TO {app_name}_user;
ALTER DATABASE {app_name}_db OWNER TO {app_name}_user;
\\q
"""

    # 2. .ENV FILE
    env_content = f"""DEBUG=False
SECRET_KEY={secret_key}
ALLOWED_HOSTS={domain},localhost,127.0.0.1
DATABASE_URL=postgres://{app_name}_user:{db_pass}@localhost:5432/{app_name}_db
"""
    if has_celery:
        env_content += f"CELERY_BROKER_URL=redis://localhost:6379/{redis_db}\n"
        env_content += f"CELERY_RESULT_BACKEND=redis://localhost:6379/{redis_db}\n"

    # 3. GUNICORN SERVICE
    web_service = f"""[Unit]
Description=Gunicorn for {app_name}
After=network.target

[Service]
User=carbonplanner
Group=www-data
WorkingDirectory={base_path}
ExecStart={base_path}/venv/bin/gunicorn --workers 3 --bind unix:{base_path}/{app_name}.sock {proj_folder}.wsgi:application

[Install]
WantedBy=multi-user.target
"""

    # 4. CELERY SERVICE
    worker_service = ""
    if has_celery:
        worker_service = f"""[Unit]
Description=Celery Worker for {app_name}
After=network.target

[Service]
Type=simple
User=carbonplanner
Group=www-data
WorkingDirectory={base_path}
ExecStart={base_path}/venv/bin/celery -A {proj_folder} worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
"""

    # 5. NGINX CONFIG
    nginx_content = f"""server {{
    listen 80;
    server_name {domain};

    location = /favicon.ico {{ access_log off; log_not_found off; }}

    location /static/ {{
        alias {base_path}/staticfiles/;
    }}

    location /media/ {{
        alias {base_path}/media/;
    }}

    location / {{
        include proxy_params;
        proxy_pass http://unix:{base_path}/{app_name}.sock;
    }}
}}
"""

    # Write files
    files = {
        "psql_setup.sql": psql_content,
        ".env": env_content,
        f"{app_name}_web.service": web_service,
        "nginx_config": nginx_content,
    }
    if has_celery:
        files[f"{app_name}_worker.service"] = worker_service

    for filename, content in files.items():
        with open(os.path.join(app_name, filename), "w") as f:
            f.write(content)

    print(f"\n✅ Success! All files generated in the '{app_name}' folder.")
    print(f"Next steps:")
    print(f"1. Run the commands in 'psql_setup.sql' on the server.")
    print(f"2. Copy .env to {base_path}/.env")
    print(f"3. Copy service files to /etc/systemd/system/")
    print(f"4. Copy nginx_config to /etc/nginx/sites-available/{app_name}")

if __name__ == "__main__":
    main()