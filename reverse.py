import os
import re
import time

import yaml


def load_config(config_file='config.yaml'):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config


def find_django_project_name():
    for root, dirs, files in os.walk('.'):
        if 'wsgi.py' in files and 'settings.py' in files:
            return os.path.basename(root)
    return None


def update_console(message):
    print(message)
    for _ in range(3):
        print('.', end='', flush=True)
        time.sleep(1)
    print()


def read_deployment_history():
    if not os.path.exists('deployment_history.log'):
        print("Deployment history log not found. Setup script may not have been run.")
        return None

    with open('deployment_history.log', 'r') as log_file:
        return log_file.readlines()


def reverse_changes(project_name, history):
    settings_path = os.path.join(project_name, 'settings.py')
    urls_path = os.path.join(project_name, 'urls.py')
    wsgi_path = os.path.join(project_name, 'wsgi.py')

    for line in reversed(history):
        action = line.split(': ', 1)[1].strip()

        if "Set DEBUG to False" in action:
            set_debug_to_true(settings_path)
        elif "Generated requirements.txt" in action:
            os.remove('requirements.txt')
        elif "Configured static files" in action:
            remove_static_file_config(settings_path)
        elif "Installed Whitenoise" in action:
            uninstall_whitenoise()
            remove_whitenoise_middleware(settings_path)
        elif "Removed SQLite configuration" in action:
            restore_sqlite_config(settings_path)
        elif "Added new database configuration" in action:
            remove_database_config(settings_path)
        elif "Created .env file" in action:
            os.remove('.env')
        elif "Updated ALLOWED_HOSTS" in action:
            reset_allowed_hosts(settings_path)
        elif "Created vercel.json" in action:
            os.remove('vercel.json')
        elif "Updated wsgi.py" in action:
            remove_app_from_wsgi(wsgi_path)
        elif "Configured static and media URL patterns" in action:
            remove_url_patterns(urls_path)
        elif "Added CSRF_TRUSTED_ORIGINS" in action:
            remove_csrf_trusted_origins(settings_path)
        elif "Configured STATIC_URL, MEDIA_URL, and MEDIA_ROOT" in action:
            remove_static_and_media_settings(settings_path)

        print(f"Reversed: {action}")


def set_debug_to_true(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'DEBUG =' in line:
                file.write('DEBUG = True\n')
            else:
                file.write(line)


def remove_whitenoise_middleware(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'whitenoise.middleware.WhiteNoiseMiddleware' in line:
                continue
            else:
                file.write(line)


def remove_static_file_config(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'STATIC_ROOT =' not in line and 'STATICFILES_STORAGE =' not in line:
                file.write(line)


def uninstall_whitenoise():
    os.system('pip uninstall -y whitenoise')


def restore_sqlite_config(settings_path):
    sqlite_config = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""
    with open(settings_path, 'r') as file:
        content = file.read()

    pattern = re.compile(r'DATABASES\s*=\s*{[^}]*}', re.DOTALL)
    if pattern.search(content):
        new_content = pattern.sub(sqlite_config.strip(), content)
    else:
        new_content = content + '\n' + sqlite_config.strip()

    with open(settings_path, 'w') as file:
        file.write(new_content.strip() + '\n')


def remove_database_config(settings_path):
    with open(settings_path, 'r') as file:
        content = file.read()

    pattern = re.compile(r'# Database settings from \.env\s*DATABASES\s*=\s*{[^}]*}', re.DOTALL)
    new_content = pattern.sub('', content)

    # Remove any leftover closing brackets
    new_content = re.sub(r'}\s*$', '', new_content, flags=re.MULTILINE)

    with open(settings_path, 'w') as file:
        file.write(new_content.strip() + '\n')


def reset_allowed_hosts(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'ALLOWED_HOSTS =' in line:
                file.write("ALLOWED_HOSTS = []\n")
            else:
                file.write(line)


def remove_app_from_wsgi(wsgi_path):
    with open(wsgi_path, 'r') as file:
        lines = file.readlines()

    with open(wsgi_path, 'w') as file:
        for line in lines:
            if 'app = application' not in line:
                file.write(line)


def remove_url_patterns(urls_path):
    with open(urls_path, 'r') as file:
        lines = file.readlines()

    with open(urls_path, 'w') as file:
        for line in lines:
            if 'urlpatterns += static(' not in line and 'settings.STATIC_URL' not in line and 'settings.MEDIA_URL' not in line:
                file.write(line)


def remove_csrf_trusted_origins(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'CSRF_TRUSTED_ORIGINS =' not in line:
                file.write(line)


def remove_static_and_media_settings(settings_path):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    with open(settings_path, 'w') as file:
        for line in lines:
            if 'MEDIA_URL =' not in line and 'MEDIA_ROOT =' not in line:
                file.write(line)


def main():
    config = load_config()
    project_name = config['project_name'] or find_django_project_name()
    if project_name is None:
        print("No Django project found.")
        return

    history = read_deployment_history()
    if history is None:
        return

    update_console("Reversing Django project configuration...")

    reverse_changes(project_name, history)

    # Remove the deployment history log
    os.remove('deployment_history.log')

    update_console("Django project configuration reversed.")


if __name__ == "__main__":
    main()
