
## 🛠️ Project Badges
[![GitHub](https://img.shields.io/github/v/release/Stoupy51/stouputils?logo=github&label=GitHub)](https://github.com/Stoupy51/stouputils/releases/latest)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/stouputils?logo=python&label=PyPI%20downloads)](https://pypi.org/project/stouputils/)
[![Documentation](https://img.shields.io/github/v/release/Stoupy51/stouputils?logo=sphinx&label=Documentation&color=purple)](https://stoupy51.github.io/stouputils/latest/)

## 📚 Project Overview
Stouputils is a collection of utility modules designed to simplify and enhance the development process.<br>
It includes a range of tools for tasks such as execution of doctests, display utilities, decorators, as well as context managers.<br>
Start now by installing the package: `pip install stouputils`.<br>

<a class="admonition" href="https://colab.research.google.com/drive/1mJ-KL-zXzIk1oKDxO6FC1SFfm-BVKG-P?usp=sharing" target="_blank" rel="noopener noreferrer">
📖 <b>Want to see examples?</b> Check out our <u>Google Colab notebook</u> with practical usage examples!
</a>

## 🚀 CLI Quick Reference

Stouputils provides a powerful command-line interface. Here's a quick example for each subcommand:

```bash
# Show version information of polars with dependency tree of depth 3
stouputils --version polars -t 3

# Run all doctests in a directory with pattern filter (fnmatch)
stouputils all_doctests "./src" "*_test"

# Repair a corrupted/obstructed zip archive
stouputils repair "./input.zip" "./output.zip"

# Create a delta backup
stouputils backup delta "./source" "./backups"

# Build and publish to PyPI (with minor version bump and no stubs)
stouputils build minor --no_stubs

# Generate changelog from git history (since a specific date, with commit URLs from origin remote, output to file)
stouputils changelog date "2026-01-01" -r origin -o "CHANGELOG.md"
```

> 📖 See the [Extensive CLI Documentation](#-extensive-cli-documentation) section below for detailed usage and all available options.

## 🚀 Project File Tree
<html>
<details style="display: none;">
<summary></summary>
<style>
.code-tree {
	border-radius: 6px; 
	padding: 16px; 
	font-family: monospace; 
	line-height: 1.45; 
	overflow: auto; 
	white-space: pre;
	background-color:rgb(43, 43, 43);
	color: #d4d4d4;
}
.code-tree a {
	color: #569cd6;
	text-decoration: none;
}
.code-tree a:hover {
	text-decoration: underline;
}
.code-tree .comment {
	color:rgb(231, 213, 48);
}
.code-tree .paren {
	color: orange;
}
</style>
</details>

<pre class="code-tree">stouputils/
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.print.html">print.py</a>         <span class="comment"># 🖨️ Utility functions for printing <span class="paren">(info, debug, warning, error, whatisit, breakpoint, colored_for_loop, ...)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.decorators.html">decorators.py</a>    <span class="comment"># 🎯 Decorators <span class="paren">(measure_time, handle_error, timeout, retry, simple_cache, abstract, deprecated, silent)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.ctx.html">ctx.py</a>           <span class="comment"># 🔇 Context managers <span class="paren">(LogToFile, MeasureTime, Muffle, DoNothing, SetMPStartMethod)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.io.html">io.py</a>            <span class="comment"># 💾 Utilities for file management <span class="paren">(json_dump, json_load, csv_dump, csv_load, read_file, super_copy, super_open, clean_path, ...)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.parallel.html">parallel.py</a>      <span class="comment"># 🔀 Utility functions for parallel processing <span class="paren">(multiprocessing, multithreading, run_in_subprocess)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.image.html">image.py</a>         <span class="comment"># 🖼️ Little utilities for image processing <span class="paren">(image_resize, auto_crop, numpy_to_gif, numpy_to_obj)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.collections.html">collections.py</a>   <span class="comment"># 🧰 Utilities for collection manipulation <span class="paren">(unique_list, at_least_n, sort_dict_keys, upsert_in_dataframe, array_to_disk)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.typing.html">typing.py</a>        <span class="comment"># 📝 Utilities for typing enhancements <span class="paren">(IterAny, JsonDict, JsonList, ..., convert_to_serializable)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.all_doctests.html">all_doctests.py</a>  <span class="comment"># ✅ Run all doctests for all modules in a given directory <span class="paren">(launch_tests, test_module_with_progress)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.backup.html">backup.py</a>        <span class="comment"># 💾 Utilities for backup management <span class="paren">(delta backup, consolidate)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.archive.html">archive.py</a>       <span class="comment"># 📦 Functions for creating and managing archives</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.config.html">config.py</a>        <span class="comment"># ⚙️ Global configuration <span class="paren">(StouputilsConfig: global options)</span></span>
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.html">applications/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.automatic_docs.html">automatic_docs.py</a>    <span class="comment"># 📚 Documentation generation utilities <span class="paren">(used to create this documentation)</span></span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.upscaler.html">upscaler/</a>            <span class="comment"># 🔎 Image & Video upscaler <span class="paren">(configurable)</span></span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.html">continuous_delivery/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.cd_utils.html">cd_utils.py</a>          <span class="comment"># 🔧 Utilities for continuous delivery</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.git.html">git.py</a>               <span class="comment"># 📜 Utilities for local git changelog generation</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.github.html">github.py</a>            <span class="comment"># 📦 Utilities for continuous delivery on GitHub <span class="paren">(upload_to_github)</span></span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.pypi.html">pypi.py</a>              <span class="comment"># 📦 Utilities for PyPI <span class="paren">(pypi_full_routine)</span></span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.pyproject.html">pyproject.py</a>         <span class="comment"># 📝 Utilities for reading, writing and managing pyproject.toml files</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.stubs.html">stubs.py</a>             <span class="comment"># 📝 Utilities for generating stub files using stubgen</span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.html">data_science/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.config.html">config/</a>              <span class="comment"># ⚙️ Configuration utilities for data science</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.dataset.html">dataset/</a>             <span class="comment"># 📊 Dataset handling <span class="paren">(dataset, dataset_loader, grouping_strategy)</span></span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.data_processing.html">data_processing/</a>     <span class="comment"># 🔄 Data processing utilities <span class="paren">(image augmentation, preprocessing)</span></span>
│   │   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.data_processing.image.html">image/</a>           <span class="comment"># 🖼️ Image processing techniques</span>
│   │   └── ...
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.models.html">models/</a>              <span class="comment"># 🧠 ML/DL model interfaces and implementations</span>
│   │   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.models.keras.html">keras/</a>           <span class="comment"># 🤖 Keras model implementations</span>
│   │   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.models.keras_utils.html">keras_utils/</a>     <span class="comment"># 🛠️ Keras utilities <span class="paren">(callbacks, losses, visualizations)</span></span>
│   │   └── ...
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.scripts.html">scripts/</a>             <span class="comment"># 📜 Data science scripts <span class="paren">(augment, preprocess, routine)</span></span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.metric_utils.html">metric_utils.py</a>      <span class="comment"># 📏 Static methods for calculating various ML metrics</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.mlflow_utils.html">mlflow_utils.py</a>      <span class="comment"># 📊 Utility functions for working with MLflow</span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.html">installer/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.common.html">common.py</a>            <span class="comment"># 🔧 Common functions used by the Linux and Windows installers modules</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.downloader.html">downloader.py</a>        <span class="comment"># ⬇️ Functions for downloading and installing programs from URLs</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.linux.html">linux.py</a>             <span class="comment"># 🐧 Linux/macOS specific implementations for installation</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.main.html">main.py</a>              <span class="comment"># 🚀 Core installation functions for installing programs from zip files or URLs</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.windows.html">windows.py</a>           <span class="comment"># 💻 Windows specific implementations for installation</span>
│   └── ...
└── ...
</pre>
</html>

## 🔧 Installation

```bash
pip install stouputils
```

### ✨ Enable Tab Completion on Linux (Optional)

For a better CLI experience, enable bash tab completion:

```bash
# Option 1: Using argcomplete's global activation
activate-global-python-argcomplete --user

# Option 2: Manual setup for bash
register-python-argcomplete stouputils >> ~/.bashrc
source ~/.bashrc
```

After enabling completion, you can use `<TAB>` to autocomplete commands:
```bash
stouputils <TAB>        # Shows: --version, -v, all_doctests, backup
stouputils all_<TAB>    # Completes to: all_doctests
```

**Note:** Tab completion works best in bash, zsh, Git Bash, or WSL on Windows.

## 📖 Extensive CLI Documentation

The `stouputils` CLI provides several powerful commands for common development tasks.

### ⚡ General Usage

```bash
stouputils <command> [options]
```

Running `stouputils` without arguments displays help with all available commands.

---

### 📌 `--version` / `-v` — Show Version Information

Display the version of stouputils and its dependencies, along with the used Python version.

```bash
# Basic usage - show stouputils version
stouputils --version
stouputils -v

# Show version for a specific package
stouputils --version numpy
stouputils -v requests

# Show dependency tree (depth 3+)
stouputils --version -t 3
stouputils -v stouputils --tree 4
```

**Options:**
| Option | Description |
|--------|-------------|
| `[package]` | Optional package name to show version for (default: stouputils) |
| `-t`, `--tree <depth>` | Show dependency tree with specified depth (≤2 for flat list, ≥3 for tree view) |

---

### ✅ `all_doctests` — Run Doctests

Execute all doctests in Python files within a directory.

```bash
# Run doctests in current directory
stouputils all_doctests

# Run doctests in specific directory
stouputils all_doctests ./src

# Run doctests with file pattern filter
stouputils all_doctests ./src "*image/*.py"
stouputils all_doctests . "*utils*"
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `[directory]` | Directory to search for Python files (default: `.`) |
| `[pattern]` | Glob pattern to filter files (default: `*`) |

**Exit codes:**
- `0`: All tests passed
- `1`: One or more tests failed

---

### 📦 `archive` — Archive Utilities

Create and repair ZIP archives.

```bash
# Show archive help
stouputils archive --help
```

#### `archive make` — Create Archive

```bash
# Basic archive creation
stouputils archive make ./my_folder ./backup.zip

# Create archive with ignore patterns
stouputils archive make ./project ./project.zip --ignore "*.pyc,__pycache__,*.log"

# Create destination directory if needed
stouputils archive make ./source ./backups/archive.zip --create-dir
```

**Arguments & Options:**
| Argument/Option | Description |
|-----------------|-------------|
| `<source>` | Source directory to archive |
| `<destination>` | Destination zip file path |
| `--ignore <patterns>` | Comma-separated glob patterns to exclude |
| `--create-dir` | Create destination directory if it doesn't exist |

#### `archive repair` — Repair Corrupted ZIP

```bash
# Repair with auto-generated output name
stouputils archive repair ./corrupted.zip

# Repair with custom output name
stouputils archive repair ./corrupted.zip ./fixed.zip
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `<input_file>` | Path to the corrupted zip file |
| `[output_file]` | Path for repaired file (default: adds `_repaired` suffix) |

---

### 💾 `backup` — Backup Utilities

Create delta backups, consolidate existing backups, and manage backup retention.

```bash
# Show backup help
stouputils backup --help
```

#### `backup delta` — Create Delta Backup

Create an incremental backup containing only new or modified files since the last backup.

```bash
# Basic delta backup
stouputils backup delta ./my_project ./backups

# Delta backup with exclusions
stouputils backup delta ./project ./backups -x "*.pyc" "__pycache__/*" "node_modules/*"
stouputils backup delta ./source ./backups --exclude "*.log" "temp/*"
```

**Arguments & Options:**
| Argument/Option | Description |
|-----------------|-------------|
| `<source>` | Source directory or file to back up |
| `<destination>` | Destination folder for backups |
| `-x`, `--exclude <patterns>` | Glob patterns to exclude (space-separated) |

#### `backup consolidate` — Consolidate Backups

Merge multiple delta backups into a single complete backup.

```bash
# Consolidate all backups up to latest.zip into one file
stouputils backup consolidate ./backups/latest.zip ./consolidated.zip
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `<backup_zip>` | Path to the latest backup ZIP file |
| `<destination_zip>` | Path for the consolidated output file |

#### `backup limit` — Limit Backup Count

Limit the number of delta backups by consolidating the oldest ones.

```bash
# Keep only the 5 most recent backups
stouputils backup limit 5 ./backups

# Allow deletion of the oldest backup (not recommended)
stouputils backup limit 5 ./backups --no-keep-oldest
```

**Arguments & Options:**
| Argument/Option | Description |
|-----------------|-------------|
| `<max_backups>` | Maximum number of backups to keep |
| `<backup_folder>` | Path to the folder containing backups |
| `--no-keep-oldest` | Allow deletion of the oldest backup (default: keep it) |

---

### 🏗️ `build` — Build and Publish to PyPI

Build and publish a Python package to PyPI using the `uv` tool. This runs a complete routine including version bumping, stub generation, building, and publishing.

```bash
# Standard build and publish (bumps patch by default)
stouputils build

# Build without generating stubs and without bumping version
stouputils build --no_stubs --no_bump

# Bump minor version before build
stouputils build minor

# Bump major version before build
stouputils build major
```

**Options:**
| Option | Description |
|--------|-------------|
| `--no_stubs` | Skip stub file generation |
| `--no_bump` | Skip version bumping (use current version) |
| `minor` | Bump minor version (e.g., 1.2.0 → 1.3.0) |
| `major` | Bump major version (e.g., 1.2.0 → 2.0.0) |

---

### 📜 `changelog` — Generate Changelog

Generate a formatted changelog from local git history.

```bash
# Show changelog help
stouputils changelog --help
```

```bash
# Generate changelog since latest tag (default)
stouputils changelog

# Generate changelog since a specific tag
stouputils changelog tag v1.9.0

# Generate changelog since a specific date
stouputils changelog date 2026/01/05
stouputils changelog date "2026-01-15 14:30:00"

# Generate changelog since a specific commit
stouputils changelog commit 847b27e

# Include commit URLs from a remote
stouputils changelog --remote origin
stouputils changelog tag v2.0.0 -r origin

# Output to a file
stouputils changelog -o CHANGELOG.md
stouputils changelog tag v1.0.0 --output docs/CHANGELOG.md
```

**Arguments & Options:**
| Argument/Option | Description |
|-----------------|-------------|
| `[mode]` | Mode for selecting commits: `tag`, `date`, or `commit` (default: `tag`) |
| `[value]` | Value for the mode (tag name, date, or commit SHA) |
| `-r`, `--remote <name>` | Remote name for commit URLs (e.g., `origin`) |
| `-o`, `--output <file>` | Output file path (default: stdout) |

**Supported date formats:**
- `YYYY/MM/DD` or `YYYY-MM-DD`
- `DD/MM/YYYY` or `DD-MM-YYYY`
- `YYYY-MM-DD HH:MM:SS`
- ISO 8601: `YYYY-MM-DDTHH:MM:SS`

---

### 📋 Examples Summary

| Command | Description |
|---------|-------------|
| `stouputils -v` | Show version |
| `stouputils -v numpy -t 3` | Show numpy version with dependency tree |
| `stouputils all_doctests ./src` | Run doctests in src directory |
| `stouputils archive make ./proj ./proj.zip` | Create archive |
| `stouputils archive repair ./bad.zip` | Repair corrupted zip |
| `stouputils backup delta ./src ./bak -x "*.pyc"` | Create delta backup |
| `stouputils backup consolidate ./bak/latest.zip ./full.zip` | Consolidate backups |
| `stouputils backup limit 5 ./bak` | Keep only 5 backups |
| `stouputils build minor` | Build with minor version bump |
| `stouputils changelog tag v1.0.0 -r origin -o CHANGELOG.md` | Generate changelog to file |

## ⭐ Star History

<html>
	<a href="https://star-history.com/#Stoupy51/stouputils&Date">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Stoupy51/stouputils&type=Date&theme=dark" />
			<source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Stoupy51/stouputils&type=Date" />
			<img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Stoupy51/stouputils&type=Date" />
		</picture>
	</a>
</html>

