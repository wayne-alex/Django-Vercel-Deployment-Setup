# Django Vercel Deployment Setup

This repository contains tools for configuring a Django project for deployment on Vercel. It includes scripts to set up and reverse configurations needed for a smooth deployment process.

## Project Overview

This project provides two key scripts:

1. **`setup.py`**: Configures a Django project for deployment on Vercel. This includes setting debug flags, configuring static files, installing necessary packages, and more.
2. **`reverse.py`**: Reverts changes made by `setup.py` in case you need to undo the configuration. This ensures that your project can return to its previous state if something goes wrong.

## Requirements

To run these scripts, you need to have `pyyaml` installed. You can install it using:

```bash
pip install pyyaml
```

## Configuration

### `config.yaml`

The `config.yaml` file contains project configuration settings for the deployment setup. Here's a brief overview of the options:

- **`project_name`**: Specify your Django project name. If left blank, the script will automatically find the project name.
- **`set_debug_false`**: Set to `true` to configure Django with `DEBUG = False`.
- **`generate_requirements`**: Set to `true` to generate a `requirements.txt` file using `pip freeze`.
- **`configure_static_files`**: Set to `true` to configure static files, install Whitenoise, and set up static files storage.
- **`configure_database`**: Set to `true` to remove SQLite configuration and prepare for a production database.

## Usage

### Running the Setup Script

1. Ensure `config.yaml` is configured according to your needs.
2. Run the setup script:

    ```bash
    python setup.py
    ```

This script will configure your Django project for deployment on Vercel according to the settings in `config.yaml`.

### Reverting Changes

If you need to revert the changes made by `setup.py`, use the `reverse.py` script:

```bash
python reverse.py
```

This will undo the changes made during the setup process based on the deployment history.

## Issues

If you encounter any issues, please open an issue in this repository. We appreciate your feedback and will work to address any problems as quickly as possible.

## Contributions

Contributions are welcome! If you have ideas for improvements or optimizations, feel free to fork the repository and submit a pull request. We encourage you to optimize and enhance the code.

## Important Notes

- **Settings Backup**: The `reverse.py` script will remove the deployment history log once the configuration is reversed. If the reverse process fails, the settings are saved in the same folder for manual recovery.
- **Optimizations**: The provided scripts are designed as a starting point. You are encouraged to optimize and adapt them to better fit your specific needs.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

