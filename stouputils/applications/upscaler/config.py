"""
This module provides configuration settings and constants for the upscaler application.

It defines the URLs for downloading dependencies like waifu2x-ncnn-vulkan and FFmpeg,
and provides a Config class with settings for upscaling operations, including output quality,
bitrates, executable paths, and command-line arguments for the underlying tools.

Configuration options include:
- Image quality settings (JPG quality)
- Video encoding parameters (bitrate, codec, etc.)
- Paths to external binaries (FFmpeg, waifu2x-ncnn-vulkan)
- Command-line arguments for upscaling and video processing
"""
# Constants
WAIFU2X_NCNN_VULKAN_RELEASES: dict[str, str] = {
	"Windows": "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-windows.zip",
	"Linux": "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-ubuntu.zip",
	"Darwin": "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-macos.zip"
}
""" URLs to download waifu2x-ncnn-vulkan from for each common platform. """
FFMPEG_RELEASES: dict[str, str] = {
	"Windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
	"Linux": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
	"Darwin": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-macos64-gpl.tar.xz"
}
""" URLs to download FFmpeg from for each common platform. """
YOUTUBE_BITRATE_RECOMMENDATIONS: dict[str, dict[str, dict[int, int]]] = {
	"SDR": {
		"standard": {  # Standard Frame Rate (24, 25, 30)
			4320: 160000,  # 8K - 160 Mbps
			2160: 45000,   # 4K - 45 Mbps
			1440: 16000,   # 2K - 16 Mbps
			1080: 8000,    # 1080p - 8 Mbps
			720: 5000,     # 720p - 5 Mbps
			480: 2500,     # 480p - 2.5 Mbps
			0: 1000        # 360p or lower - 1 Mbps
		},
		"high": {  # High Frame Rate (48, 50, 60)
			4320: 240000,  # 8K - 240 Mbps
			2160: 68000,   # 4K - 68 Mbps
			1440: 24000,   # 2K - 24 Mbps
			1080: 12000,   # 1080p - 12 Mbps
			720: 7500,     # 720p - 7.5 Mbps
			480: 4000,     # 480p - 4 Mbps
			0: 1500        # 360p or lower - 1.5 Mbps
		}
	},
	"HDR": {
		"standard": {  # Standard Frame Rate (24, 25, 30)
			4320: 200000,  # 8K - 200 Mbps
			2160: 56000,   # 4K - 56 Mbps
			1440: 20000,   # 2K - 20 Mbps
			1080: 10000,   # 1080p - 10 Mbps
			0: 6500        # 720p or lower - 6.5 Mbps
		},
		"high": {  # High Frame Rate (48, 50, 60)
			4320: 300000,  # 8K - 300 Mbps
			2160: 85000,   # 4K - 85 Mbps
			1440: 30000,   # 2K - 30 Mbps
			1080: 15000,   # 1080p - 15 Mbps
			0: 9500        # 720p or lower - 9.5 Mbps
		}
	}
}
""" YouTube bitrate recommendations for different resolutions and frame rates.

This dictionary contains recommended bitrates for YouTube uploads based on:
- SDR vs HDR content
- Standard frame rate (24, 25, 30 fps) vs high frame rate (48, 50, 60 fps)
- Video resolution (from 360p up to 8K)

The values are in kbps (kilobits per second).

Source: https://support.google.com/youtube/answer/1722171
"""

# Configuration class
class Config:
	""" Configuration class for the upscaler. """
	JPG_QUALITY: int = 95
	""" JPG quality for the output images. (Range: 0-100) """

	VIDEO_FINAL_BITRATE: int = -1
	""" Video final bitrate for the output video. -1 for YouTube recommended bitrate based on the video resolution. """

	FFMPEG_EXECUTABLE: str = "ffmpeg"
	""" Path to the ffmpeg executable, default is "ffmpeg" in the PATH. """

	FFMPEG_ARGS: tuple[str, ...] = (
		"-c:a", "copy",         # Copy the audio without re-encoding
		"-c:v", "hevc_nvenc",   # Encode the video
		"-map", "0:v:0",        # Map the first input -i (frames) as video
		"-map", "1:a:0?",       # Map the second input -i (sound) as audio, with '?' to ignore if no audio stream
		"-preset", "slow",      # Set the encoding preset to slow (slower but better quality)
		"-y",					# Overwrite the output file if it exists
	)
	""" Additional arguments sent to the ffmpeg executable when calling subprocess.run(). """

	FFPROBE_EXECUTABLE: str = "ffprobe"
	""" Path to the ffprobe executable, default is "ffprobe" in the PATH. Used to get the framerate of the video. """

	FFMPEG_CHECK_HELP_TEXT: str = "usage: ffmpeg [options]"
	""" If this text is present in the output of the ffmpeg executable, it means it's installed correctly. """

	UPSCALER_EXECUTABLE: str = "waifu2x-ncnn-vulkan"
	""" Path to the upscaler executable, default is "waifu2x-ncnn-vulkan" in the PATH. """

	UPSCALER_ARGS: tuple[str, ...] = (
		"-i", "INPUT_PATH",     # Input file path
		"-o", "OUTPUT_PATH",    # Output file path
		"-s", "UPSCALE_RATIO",  # Upscaling ratio
		"-n", "3",              # Noise level
	)
	""" Arguments sent to the upscaler executable when calling subprocess.run(). """

	UPSCALER_EXECUTABLE_HELP_TEXT: str = "Usage: waifu2x-ncnn-vulkan -i"
	""" If this text is present in the output of the upscaler executable, it means it's installed correctly. """

	SLIGHTLY_FASTER_MODE: bool = False
	""" If True, the upscaler executable will be called once, which is slightly faster but you can't see the progress. """

	# Variables
	upscaler_executable_checked: bool = False
	""" Whether the upscaler executable has been checked for. """

	ffmpeg_executable_checked: bool = False
	""" Whether the ffmpeg executable has been checked for. """

