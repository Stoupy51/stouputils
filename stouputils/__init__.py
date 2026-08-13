""" Stouputils is a collection of utility modules designed to simplify and enhance the development process.
It includes a range of tools for tasks such as execution of doctests, display utilities, decorators, as well as context managers.

Check the documentation for more details: https://stoupy51.github.io/stouputils/
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.__main__",
	"stouputils._deprecated",
	"stouputils.all_doctests",
	"stouputils.archive",
	"stouputils.backup",
	"stouputils.collections",
	"stouputils.continuous_delivery",
	"stouputils.ctx",
	"stouputils.decorators",
	"stouputils.image",
	"stouputils.io",
	"stouputils.lock",
	"stouputils.parallel",
	"stouputils.print",
	"stouputils.typing",
	"stouputils.version_pkg",
	"typing",
})

# Imports
from typing import TYPE_CHECKING

from .__main__ import main as main  # type: ignore
from ._deprecated import (
	colored_for_loop as colored_for_loop,
	super_csv_dump as super_csv_dump,
	super_csv_load as super_csv_load,
	super_json_dump as super_json_dump,
	super_json_load as super_json_load,
)
from .all_doctests import (
	find_missing_reexports as find_missing_reexports,
	launch_tests as launch_tests,
	module_public_names as module_public_names,
	test_module_with_progress as test_module_with_progress,
)
from .archive import (
	archive_cli as archive_cli,
	make_archive as make_archive,
	repair_zip_file as repair_zip_file,
)
from .backup import (
	add_file_to_zip as add_file_to_zip,
	backup_cli as backup_cli,
	consolidate_backups as consolidate_backups,
	create_delta_backup as create_delta_backup,
	extract_hash_from_zipinfo as extract_hash_from_zipinfo,
	get_all_previous_backups as get_all_previous_backups,
	get_backup_sort_key as get_backup_sort_key,
	get_file_hash as get_file_hash,
	is_file_in_any_previous_backup as is_file_in_any_previous_backup,
	limit_backups as limit_backups,
)
from .collections import (
	FeistelHelpers as FeistelHelpers,
	affine_permutation_generator as affine_permutation_generator,
	at_least_n as at_least_n,
	feistel_permutation_generator as feistel_permutation_generator,
	sort_dict_keys as sort_dict_keys,
	unique_list as unique_list,
	upsert_in_dataframe as upsert_in_dataframe,
)
from .continuous_delivery import (
	GITHUB_API_URL as GITHUB_API_URL,
	GITLAB_URL as GITLAB_URL,
	PlatformConfig as PlatformConfig,
	build_github_config as build_github_config,
	build_gitlab_config as build_gitlab_config,
	build_package as build_package,
	changelog_cli as changelog_cli,
	check_existing_tag as check_existing_tag,
	clean_stubs_directory as clean_stubs_directory,
	clean_version as clean_version,
	create_github_release as create_github_release,
	create_github_tag as create_github_tag,
	create_gitlab_release as create_gitlab_release,
	create_gitlab_tag as create_gitlab_tag,
	create_release as create_release,
	create_tag_on_branch as create_tag_on_branch,
	create_url_formatter as create_url_formatter,
	delete_github_release as delete_github_release,
	delete_github_tag as delete_github_tag,
	delete_gitlab_release as delete_gitlab_release,
	delete_gitlab_tag as delete_gitlab_tag,
	delete_resource as delete_resource,
	delete_resource_unconditional as delete_resource_unconditional,
	detect_host_type as detect_host_type,
	extract_github_commit_data as extract_github_commit_data,
	extract_gitlab_commit_data as extract_gitlab_commit_data,
	format_changelog as format_changelog,
	format_toml_lists as format_toml_lists,
	generate_changelog as generate_changelog,
	generate_local_changelog as generate_local_changelog,
	generate_stubs as generate_stubs,
	get_commits_since_commit as get_commits_since_commit,
	get_commits_since_date as get_commits_since_date,
	get_commits_since_tag as get_commits_since_tag,
	get_github_commit_date as get_github_commit_date,
	get_github_sha as get_github_sha,
	get_gitlab_commit_date as get_gitlab_commit_date,
	get_gitlab_sha as get_gitlab_sha,
	get_latest_tag as get_latest_tag,
	get_local_tags as get_local_tags,
	get_remotes as get_remotes,
	get_version_from_pyproject as get_version_from_pyproject,
	handle_existing_tag as handle_existing_tag,
	handle_response as handle_response,
	increment_version_from_input as increment_version_from_input,
	increment_version_from_pyproject as increment_version_from_pyproject,
	load_credentials as load_credentials,
	log_success as log_success,
	paginate_api as paginate_api,
	parse_commit_log as parse_commit_log,
	parse_commit_message as parse_commit_message,
	parse_date_fallback as parse_date_fallback,
	parse_remote_url as parse_remote_url,
	prompt_delete_existing as prompt_delete_existing,
	publish_release as publish_release,
	pypi_full_routine as pypi_full_routine,
	pypi_full_routine_using_uv as pypi_full_routine_using_uv,
	read_pyproject as read_pyproject,
	run_git_command as run_git_command,
	stubs_full_routine as stubs_full_routine,
	update_pip_and_required_packages as update_pip_and_required_packages,
	upload_files as upload_files,
	upload_github_assets as upload_github_assets,
	upload_gitlab_assets as upload_gitlab_assets,
	upload_package as upload_package,
	upload_to_github as upload_to_github,
	upload_to_gitlab as upload_to_gitlab,
	validate_github_config as validate_github_config,
	validate_github_credentials as validate_github_credentials,
	validate_gitlab_config as validate_gitlab_config,
	validate_gitlab_credentials as validate_gitlab_credentials,
	validate_required_keys as validate_required_keys,
	version_to_float as version_to_float,
	write_pyproject as write_pyproject,
)
from .ctx import (
	AbstractBothContextManager as AbstractBothContextManager,
	DoNothing as DoNothing,
	ErrorLevelDetector as ErrorLevelDetector,
	LogToFile as LogToFile,
	MeasureTime as MeasureTime,
	Muffle as Muffle,
	NullContextManager as NullContextManager,
	SetMPStartMethod as SetMPStartMethod,
)
from .decorators import (
	ALL_CACHES as ALL_CACHES,
	KWARGS_MARKER as KWARGS_MARKER,
	MISSING as MISSING,
	WRAPPED_ATTRIBUTE as WRAPPED_ATTRIBUTE,
	LogLevels as LogLevels,
	abstract as abstract,
	clear_simple_caches as clear_simple_caches,
	deprecated as deprecated,
	get_function_name as get_function_name,
	get_wrapper_name as get_wrapper_name,
	handle_error as handle_error,
	measure_time as measure_time,
	retry as retry,
	safe_wraps as safe_wraps,
	set_wrapper_name as set_wrapper_name,
	silent as silent,
	simple_cache as simple_cache,
	timeout as timeout,
)
from .image import (
	T as T,
	add_default_colors_to_segments as add_default_colors_to_segments,
	auto_crop as auto_crop,
	extract_verts_faces_from_segment as extract_verts_faces_from_segment,
	image_resize as image_resize,
	numpy_segments_to_obj as numpy_segments_to_obj,
	numpy_to_gif as numpy_to_gif,
	numpy_to_obj as numpy_to_obj,
)
from .io import (
	clean_path as clean_path,
	copytree_with_progress as copytree_with_progress,
	create_bind_mount as create_bind_mount,
	create_junction as create_junction,
	csv_dump as csv_dump,
	csv_load as csv_load,
	get_root_path as get_root_path,
	is_junction as is_junction,
	json_dump as json_dump,
	json_load as json_load,
	read_file as read_file,
	redirect_cli as redirect_cli,
	redirect_folder as redirect_folder,
	relative_path as relative_path,
	replace_tilde as replace_tilde,
	safe_close as safe_close,
	super_copy as super_copy,
	super_open as super_open,
)
from .lock import (
	BaseTicketQueue as BaseTicketQueue,
	FileTicketQueue as FileTicketQueue,
	LockError as LockError,
	LockFifo as LockFifo,
	LockTimeoutError as LockTimeoutError,
	RedisLockFifo as RedisLockFifo,
	RedisTicketQueue as RedisTicketQueue,
	RLockFifo as RLockFifo,
	resolve_acquire_defaults as resolve_acquire_defaults,
	resolve_path as resolve_path,
)
from .parallel import (
	CPU_COUNT as CPU_COUNT,
	CaptureOutput as CaptureOutput,
	PipeWriter as PipeWriter,
	RemoteSubprocessError as RemoteSubprocessError,
	capture_subprocess_output as capture_subprocess_output,
	delayed_call as delayed_call,
	doctest_slow as doctest_slow,
	doctest_square as doctest_square,
	handle_parameters as handle_parameters,
	multiprocessing as multiprocessing,
	multithreading as multithreading,
	nice_wrapper as nice_wrapper,
	normalize_parallel_params as normalize_parallel_params,
	process_title_wrapper as process_title_wrapper,
	resolve_process_title as resolve_process_title,
	run_in_subprocess as run_in_subprocess,
	run_sequential as run_sequential,
	set_process_priority as set_process_priority,
	starmap as starmap,
)
from .print import (
	BAR_FORMAT as BAR_FORMAT,
	BLUE as BLUE,
	BOLD as BOLD,
	CYAN as CYAN,
	GREEN as GREEN,
	LINE_UP as LINE_UP,
	LINEUP_RE as LINEUP_RE,
	MAGENTA as MAGENTA,
	RED as RED,
	RESET as RESET,
	YELLOW as YELLOW,
	PrintMemory as PrintMemory,
	TeeMultiOutput as TeeMultiOutput,
	alt_debug as alt_debug,
	alt_debugc as alt_debugc,
	breakpoint as breakpoint,
	breakpointc as breakpointc,
	colored as colored,
	current_time as current_time,
	debug as debug,
	debugc as debugc,
	error as error,
	errorc as errorc,
	format_colored as format_colored,
	info as info,
	infoc as infoc,
	is_same_print as is_same_print,
	progress as progress,
	progress_bar as progress_bar,
	progressc as progressc,
	remove_ansi as remove_ansi,
	remove_colors as remove_colors,
	suggestion as suggestion,
	suggestionc as suggestionc,
	warning as warning,
	warningc as warningc,
	whatisit as whatisit,
	whatisitc as whatisitc,
)
from .typing import (
	CallableAny as CallableAny,
	ClassInfo as ClassInfo,
	IterAny as IterAny,
	JsonDict as JsonDict,
	JsonList as JsonList,
	JsonMap as JsonMap,
	JsonMutMap as JsonMutMap,
	convert_to_serializable as convert_to_serializable,
	is_generic_instance as is_generic_instance,
	is_sequence as is_sequence,
)
from .version_pkg import (
	show_version as show_version,
	show_version_cli as show_version_cli,
)

if TYPE_CHECKING:
	__version__: str
	""" Version of the installed package, "0.0.0-dev" when running from a source tree. """
else:
	def __getattr__(name: str) -> object:
		""" Resolve __version__ and submodules on first access rather than at import time.

		Reading the installed metadata costs about half of the package import time, and submodules
		deferred by PEP 810 are not bound as attributes until one of their names is used.
		"""
		if name == "__version__":
			from importlib.metadata import PackageNotFoundError, version as importlib_version
			try:
				globals()["__version__"] = importlib_version("stouputils")
			except PackageNotFoundError:
				globals()["__version__"] = "0.0.0-dev"
			return globals()["__version__"]
		if not name.startswith("__"):
			from importlib import import_module
			try:
				return import_module(f".{name}", __name__)
			except ImportError:
				pass
		raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

