import json
import os
import re
import subprocess
import time

import yaml


def load_config(config_file='config.yaml'):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config


def find_django_project_name():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Walk through the directory tree starting from the script's directory
    for root, dirs, files in os.walk(script_dir):
        if 'wsgi.py' in files and 'settings.py' in files:
            return os.path.basename(root)

    return None


def update_console(message):
    print(message)
    for _ in range(3):
        print('.', end='', flush=True)
        time.sleep(1)
    print()


def log_change(change_description):
    with open('deployment_history.log', 'a') as log_file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp}: {change_description}\n")


def add_os_import(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    # Check if 'import os' is already in the file
    if any('import os' in line for line in lines):
        print(f"'import os' already present in {settings_path}.")
        return

    with open(settings_path, 'w') as file:
        file.write("import os\n")
        for line in lines:
            file.write(line)

    print(f"Added 'import os' to {settings_path}.")


def set_debug_to_false(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'DEBUG =' in line:
                file.write('DEBUG = False\n')
                log_change("Set DEBUG to False")
            else:
                file.write(line)


def generate_requirements():
    os.system('pip freeze > requirements.txt')
    log_change("Generated requirements.txt")


def configure_static_files(settings_path):
    with open(settings_path, 'a') as file:
        file.write("\n")
        file.write("STATIC_ROOT = BASE_DIR / 'staticfiles'\n")
        file.write("STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'\n")

    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'MIDDLEWARE' in line:
                file.write(line)
                file.write("    'django.middleware.security.SecurityMiddleware',\n")
                file.write("    'whitenoise.middleware.WhiteNoiseMiddleware',\n")
            elif 'django.middleware.security.SecurityMiddleware' in line:
                continue
            else:
                file.write(line)

    subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'])
    log_change("Configured static files and added Whitenoise middleware")


def add_whitenoise():
    subprocess.run(['pip', 'install', 'whitenoise'])
    log_change("Installed Whitenoise")


def configure_database(settings_path, env_file):
    remove_sqlite_config(settings_path)
    add_database_config(settings_path)
    create_env_file(env_file)


def remove_sqlite_config(settings_path):
    with open(settings_path, 'r') as file:
        content = file.read()

    pattern = re.compile(r'DATABASES\s*=\s*{[^}]*}', re.DOTALL)
    new_content = pattern.sub('', content)

    # Remove any leftover closing brackets
    new_content = re.sub(r'}\s*$', '', new_content, flags=re.MULTILINE)

    with open(settings_path, 'w') as file:
        file.write(new_content.strip())
    log_change("Removed SQLite configuration")


def add_load_dotenv_import(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    # Check if 'from dotenv import load_dotenv' and 'load_dotenv()' are already present
    import_line_present = any('from dotenv import load_dotenv' in line for line in lines)
    load_dotenv_call_present = any('load_dotenv()' in line for line in lines)

    if import_line_present and load_dotenv_call_present:
        print(f"'from dotenv import load_dotenv' and 'load_dotenv()' already present in {settings_path}.")
        return

    with open(settings_path, 'w') as file:
        for line in lines:
            file.write(line)
            if line.strip() == 'import os':
                if not import_line_present:
                    file.write("from dotenv import load_dotenv\n")
                if not load_dotenv_call_present:
                    file.write("\n# Load environment variables from the .env file\n")
                    file.write("load_dotenv()\n")

    print(f"Added 'from dotenv import load_dotenv' and 'load_dotenv()' to {settings_path}.")
    log_change("Added 'from dotenv import load_dotenv' and 'load_dotenv()' to settings.py")


def add_database_config(settings_path):
    add_os_import(settings_path)
    add_load_dotenv_import(settings_path)
    db_config = """
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASE_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}
"""
    with open(settings_path, 'a') as file:
        file.write("\n# Database settings from .env\n")
        file.write(db_config)
    log_change("Added new database configuration")


def create_env_file(env_file):
    if not os.path.exists(env_file):
        with open(env_file, 'w') as file:
            file.write("DATABASE_ENGINE=django.db.backends.postgresql\n")
            file.write("DATABASE_NAME=your_db_name\n")
            file.write("DATABASE_USER=your_db_user\n")
            file.write("DATABASE_PASSWORD=your_db_password\n")
            file.write("DATABASE_HOST=your_db_host\n")
            file.write("DATABASE_PORT=your_db_port\n")
        print(f"{env_file} created with placeholders.")
        log_change("Created .env file with database placeholders")


def set_allowed_hosts(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'ALLOWED_HOSTS =' in line:
                file.write("ALLOWED_HOSTS = ['.vercel.app']\n")
                log_change("Updated ALLOWED_HOSTS")
            else:
                file.write(line)


def create_vercel_json(project_name):
    vercel_config = {
        "builds": [{
            "src": f"{project_name}/wsgi.py",
            "use": "@vercel/python",
            "config": {"maxLambdaSize": "15mb", "runtime": "python3.9"}
        }],
        "routes": [
            {
                "src": "/(.*)",
                "dest": f"{project_name}/wsgi.py"
            }
        ]
    }

    with open('vercel.json', 'w') as file:
        json.dump(vercel_config, file, indent=4)
    print("vercel.json created.")
    log_change("Created vercel.json")


def replace_psycopg2_with_psycopg2_binary(file_path):
    try:
        # Read the content of the requirements.txt file
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Open the file in write mode to update its content
        with open(file_path, 'w') as file:
            for line in lines:
                # Replace psycopg2 with psycopg2-binary
                if 'psycopg2==' in line:
                    file.write(line.replace('psycopg2==', 'psycopg2-binary=='))
                else:
                    file.write(line)

        print(f"Updated {file_path} successfully.")
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def update_wsgi(project_name):
    wsgi_path = os.path.join(project_name, 'wsgi.py')
    with open(wsgi_path, 'a') as file:
        file.write("\napp = application\n")
    log_change("Updated wsgi.py to include 'app = application'")


def configure_url_patterns(project_name):
    urls_path = os.path.join(project_name, 'urls.py')
    with open(urls_path, 'r') as file:
        content = file.read()

    if 'from django.conf import settings' not in content:
        content = "from django.conf import settings\n" + content
    if 'from django.conf.urls.static import static' not in content:
        content = "from django.conf.urls.static import static\n" + content

    if 'urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)' not in content:
        content += "\n\nif settings.DEBUG:\n"
        content += "    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\n"
        content += "    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\n"

    with open(urls_path, 'w') as file:
        file.write(content)

    log_change("Configured static and media URL patterns in urls.py")


def add_csrf_trusted_origins(settings_path):
    with open(settings_path, 'a') as file:
        file.write("\nCSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']\n")
    log_change("Added CSRF_TRUSTED_ORIGINS setting")


def configure_static_and_media_settings(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    # Check if the settings are already present
    static_url_present = any('STATIC_URL' in line for line in lines)
    media_url_present = any('MEDIA_URL' in line for line in lines)
    media_root_present = any('MEDIA_ROOT' in line for line in lines)

    with open(settings_path, 'a') as file:
        if not static_url_present:
            file.write("\nSTATIC_URL = '/static/'\n")
        if not media_url_present:
            file.write("MEDIA_URL = '/media/'\n")
        if not media_root_present:
            file.write("MEDIA_ROOT = BASE_DIR / 'media'\n")

    if not (static_url_present and media_url_present and media_root_present):
        log_change("Configured STATIC_URL, MEDIA_URL, and MEDIA_ROOT settings")


def main():
    config = load_config()
    project_name = config['project_name'] or find_django_project_name()
    if project_name is None:
        print("No Django project found.")
        return

    update_console("Configuring Django project for Vercel deployment...")

    settings_path = os.path.join(project_name, 'settings.py')
    env_file = '.env'

    if config['set_debug_false']:
        set_debug_to_false(settings_path)

    if config['configure_static_files']:
        configure_static_files(settings_path)
        add_whitenoise()
        configure_static_and_media_settings(settings_path)

    if config['configure_database']:
        configure_database(settings_path, env_file)

    if config['generate_requirements']:
        generate_requirements()

    set_allowed_hosts(settings_path)
    add_csrf_trusted_origins(settings_path)
    update_wsgi(project_name)
    replace_psycopg2_with_psycopg2_binary('requirements.txt')
    create_vercel_json(project_name)

    update_console("Django project configured for Vercel deployment.")


if __name__ == "__main__":
    main()
