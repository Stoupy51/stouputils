
# Example of use:
# py examples/delta_backup.py delta "src" "backup" -x "*pycache*"

if __name__ == "__main__":
	import stouputils.backup as app
	app.backup_cli()

