# 🛠️ Project Badges
[![GitHub](https://img.shields.io/github/v/release/Stoupy51/stouputils?logo=github&label=GitHub)](https://github.com/Stoupy51/stouputils/releases/latest)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/stouputils?logo=python&label=PyPI%20downloads)](https://pypi.org/project/stouputils/)
[![Documentation](https://img.shields.io/github/v/release/Stoupy51/stouputils?logo=sphinx&label=Documentation&color=purple)](https://stoupy51.github.io/stouputils/latest/)

<br>

# 📚 Project Overview
Stouputils is a collection of utility modules designed to simplify and enhance the development process.<br>
It includes a range of tools for tasks such as execution of doctests, display utilities, decorators, as well as context managers.

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


# 🚀 Project File Tree
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
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.collections.html">collections.py</a>   <span class="comment"># 🧰 Utilities for collection manipulation <span class="paren">(unique_list, sort_dict_keys, upsert_in_dataframe, array_to_disk)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.all_doctests.html">all_doctests.py</a>  <span class="comment"># ✅ Run all doctests for all modules in a given directory <span class="paren">(launch_tests, test_module_with_progress)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.backup.html">backup.py</a>        <span class="comment"># 💾 Utilities for backup management <span class="paren">(delta backup, consolidate)</span></span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.archive.html">archive.py</a>       <span class="comment"># 📦 Functions for creating and managing archives</span>
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.html">applications/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.automatic_docs.html">automatic_docs.py</a>    <span class="comment"># 📚 Documentation generation utilities <span class="paren">(used to create this documentation)</span></span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.upscaler.html">upscaler/</a>            <span class="comment"># 🔎 Image & Video upscaler <span class="paren">(configurable)</span></span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.html">continuous_delivery/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.cd_utils.html">cd_utils.py</a>          <span class="comment"># 🔧 Utilities for continuous delivery</span>
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

