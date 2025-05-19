# 🛠️ Project Badges
[![GitHub](https://img.shields.io/github/v/release/Stoupy51/stouputils?logo=github&label=GitHub)](https://github.com/Stoupy51/stouputils/releases/latest)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/stouputils?logo=python&label=PyPI%20downloads)](https://pypi.org/project/stouputils/)
[![Documentation](https://img.shields.io/github/v/release/Stoupy51/stouputils?logo=sphinx&label=Documentation&color=purple)](https://stoupy51.github.io/stouputils/latest/)

<br>

# 📚 Project Overview
Stouputils is a collection of utility modules designed to simplify and enhance the development process.<br>
It includes a range of tools for tasks such as execution of doctests, display utilities, decorators, as well as context managers.


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
</style>
</details>

<pre class="code-tree">stouputils/
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.html">applications/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.automatic_docs.html">automatic_docs.py</a>    <span class="comment"># 📚 Documentation generation utilities (used to create this documentation)</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.applications.upscaler.html">upscaler/</a>            <span class="comment"># 🔎 Image & Video upscaler (configurable)</span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.html">continuous_delivery/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.cd_utils.html">cd_utils.py</a>          <span class="comment"># 🔧 Common utilities for continuous delivery</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.github.html">github.py</a>            <span class="comment"># 📦 GitHub utilities (upload_to_github)</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.pypi.html">pypi.py</a>              <span class="comment"># 📦 PyPI utilities (pypi_full_routine)</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.continuous_delivery.pyproject.html">pyproject.py</a>         <span class="comment"># 📝 Pyproject.toml utilities</span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.html">data_science/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.config.html">config/</a>              <span class="comment"># ⚙️ Configuration utilities for data science</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.dataset.html">dataset/</a>             <span class="comment"># 📊 Dataset handling (dataset, dataset_loader, grouping_strategy)</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.data_processing.html">data_processing/</a>     <span class="comment"># 🔄 Data processing utilities (image augmentation, preprocessing)</span>
│   │   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.data_processing.image.html">image/</a>           <span class="comment"># 🖼️ Image processing techniques</span>
│   │   └── ...
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.models.html">models/</a>              <span class="comment"># 🧠 ML/DL model interfaces and implementations</span>
│   │   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.models.keras.html">keras/</a>           <span class="comment"># 🤖 Keras model implementations</span>
│   │   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.models.keras_utils.html">keras_utils/</a>     <span class="comment"># 🛠️ Keras utilities (callbacks, losses, visualizations)</span>
│   │   └── ...
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.scripts.html">scripts/</a>             <span class="comment"># 📜 Data science scripts (augment, preprocess, routine)</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.metric_utils.html">metric_utils.py</a>      <span class="comment"># 📏 Metrics utilities for ML/DL models</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.data_science.mlflow_utils.html">mlflow_utils.py</a>      <span class="comment"># 📊 MLflow integration utilities</span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.dont_look.html">dont_look/</a>               <span class="comment"># 🙈 Internal utilities (zip_file_override)</span>
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.html">installer/</a>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.common.html">common.py</a>            <span class="comment"># 🔧 Common installer utilities</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.downloader.html">downloader.py</a>        <span class="comment"># ⬇️ File download utilities</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.linux.html">linux.py</a>             <span class="comment"># 🐧 Linux-specific installer utilities</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.main.html">main.py</a>              <span class="comment"># 🚀 Main installer functionality</span>
│   ├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.installer.windows.html">windows.py</a>           <span class="comment"># 💻 Windows-specific installer utilities</span>
│   └── ...
│
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.all_doctests.html">all_doctests.py</a>          <span class="comment"># ✅ Execution of all doctests for a given path</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.archive.html">archive.py</a>               <span class="comment"># 📦 Archive utilities (zip, repair_zip)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.backup.html">backup.py</a>                <span class="comment"># 📦 Backup utilities (delta backup, consolidate)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.collections.html">collections.py</a>           <span class="comment"># 🧰 Collection utilities (unique_list)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.ctx.html">ctx.py</a>                   <span class="comment"># 🚫 Context managers (Muffle, LogToFile)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.decorators.html">decorators.py</a>            <span class="comment"># 🎯 Decorators (silent, measure_time, error_handler, simple_cache)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.image.html">image.py</a>                 <span class="comment"># 🖼️ Image utilities (image_resize)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.io.html">io.py</a>                    <span class="comment"># 💻 I/O utilities (file management, json)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.parallel.html">parallel.py</a>              <span class="comment"># 🧑‍🤝‍🧑 Parallel processing (multiprocessing, multithreading)</span>
├── <a href="https://stoupy51.github.io/stouputils/latest/modules/stouputils.print.html">print.py</a>                 <span class="comment"># 🖨️ Display utilities (info, debug, warning, error)</span>
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

