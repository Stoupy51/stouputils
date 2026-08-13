""" Application-specific utilities and tools.

This module provides higher-level utilities for specific application needs:

Automatic Documentation:

- Automatic documentation generation with Sphinx (:py:func:`~automatic_docs.sphinx.sphinx_docs`) or Zensical (:py:func:`~automatic_docs.zensical.zensical_docs`).
- Support for multi-version documentation
- GitHub Pages integration
- Markdown to RST conversion

Upscaler:

- Utilities to upscale **images** and **videos** using external tools (defaults to ``waifu2x-ncnn-vulkan`` and ``ffmpeg``).
- Image utilities: :py:func:`~upscaler.image.upscale`, :py:func:`~upscaler.image.upscale_images`, :py:func:`~upscaler.image.upscale_folder`, :py:func:`~upscaler.image.convert_frame`, and helpers to manage temporary folders and resume partial work.
- Video utilities: extract frames with ``ffmpeg``, upscale frames, recombine frames into a final video (preserves audio),
  compute recommended bitrates using YouTube recommendations, and a :py:func:`~upscaler.video.video_upscaler_cli` convenience entry point for batch processing.
- Configuration and installer helpers: :py:class:`~upscaler.config.Config`, release lists like :py:data:`~upscaler.config.WAIFU2X_NCNN_VULKAN_RELEASES` and :py:data:`~upscaler.config.FFMPEG_RELEASES`, and :py:data:`~upscaler.config.YOUTUBE_BITRATE_RECOMMENDATIONS` mapping for bitrate selection.

Example usage:

.. code-block:: python

	# Upscale images
	from upscaler import upscale, upscale_folder

	# Upscale videos (CLI helper)
	import upscaler as upscaler
	upscaler.video_upscaler_cli("input", "progress", "output")
"""  # noqa: E501

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .automatic_docs import (
	CUSTOM_CSS as CUSTOM_CSS,
	DEFAULT_DARK_STYLE as DEFAULT_DARK_STYLE,
	DEFAULT_LIGHT_STYLE as DEFAULT_LIGHT_STYLE,
	DIRECTIVE_PATTERN as DIRECTIVE_PATTERN,
	FORGES as FORGES,
	VERBATIM_DIRECTIVES as VERBATIM_DIRECTIVES,
	ForgeUrls as ForgeUrls,
	VSCodeDarkPlusStyle as VSCodeDarkPlusStyle,
	VSCodeLightPlusStyle as VSCodeLightPlusStyle,
	VSCodeSemanticFilter as VSCodeSemanticFilter,
	check_base_dependencies as check_base_dependencies,
	check_dependencies as check_dependencies,
	connect_docstring_fixes as connect_docstring_fixes,
	download_asset as download_asset,
	fix_doctest_blocks as fix_doctest_blocks,
	generate_api_pages as generate_api_pages,
	generate_documentation as generate_documentation,
	generate_index_md as generate_index_md,
	generate_redirect_html as generate_redirect_html,
	generate_version_selector as generate_version_selector,
	get_edit_url as get_edit_url,
	get_source_url as get_source_url,
	get_sphinx_conf_content as get_sphinx_conf_content,
	get_theme_options as get_theme_options,
	get_versions_from_github as get_versions_from_github,
	get_zensical_config_content as get_zensical_config_content,
	process_docstring as process_docstring,
	python_literal as python_literal,
	sphinx_docs as sphinx_docs,
	update_documentation as update_documentation,
	write_custom_css as write_custom_css,
	zensical_docs as zensical_docs,
)
from .upscaler import (
	FFMPEG_RELEASES as FFMPEG_RELEASES,
	WAIFU2X_NCNN_VULKAN_RELEASES as WAIFU2X_NCNN_VULKAN_RELEASES,
	YOUTUBE_BITRATE_RECOMMENDATIONS as YOUTUBE_BITRATE_RECOMMENDATIONS,
	Config as Config,
	check_ffmpeg_executable as check_ffmpeg_executable,
	check_upscaler_executable as check_upscaler_executable,
	convert_frame as convert_frame,
	create_temp_dir_for_not_upscaled as create_temp_dir_for_not_upscaled,
	get_all_files as get_all_files,
	get_recommended_bitrate as get_recommended_bitrate,
	upscale as upscale,
	upscale_folder as upscale_folder,
	upscale_images as upscale_images,
	upscale_video as upscale_video,
	video_upscaler_cli as video_upscaler_cli,
)

