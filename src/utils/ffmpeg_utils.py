import sys
import os
import subprocess

def get_ffmpeg_path():
    """
    Get the path to the ffmpeg binary based on platform and compilation state.
    
    When the application is frozen (compiled with PyInstaller), ffmpeg binaries
    are bundled in the temporary directory. Otherwise, use system ffmpeg.
    
    Returns:
        str: Path to the ffmpeg binary
    """
    ffmpeg_name = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'
    
    if getattr(sys, 'frozen', False):
        # Application is frozen (compiled) - look in the PyInstaller temp directory
        return os.path.join(sys._MEIPASS, ffmpeg_name)
    
    # Development mode - use system ffmpeg
    return ffmpeg_name

def get_ffprobe_path():
    """
    Get the path to the ffprobe binary based on platform and compilation state.
    
    When the application is frozen (compiled with PyInstaller), ffprobe binaries
    are bundled in the temporary directory. Otherwise, use system ffprobe.
    
    Returns:
        str: Path to the ffprobe binary
    """
    ffprobe_name = 'ffprobe.exe' if sys.platform == 'win32' else 'ffprobe'
    
    if getattr(sys, 'frozen', False):
        # Application is frozen (compiled) - look in the PyInstaller temp directory
        return os.path.join(sys._MEIPASS, ffprobe_name)
    
    # Development mode - use system ffprobe
    return ffprobe_name

def setup_ffmpeg_environment():
    """
    Set up the Qt multimedia environment to use bundled FFmpeg when compiled.
    This ensures video playback works correctly in compiled applications.
    """
    # Force FFmpeg backend for cross-platform video codec support
    os.environ['QT_MEDIA_BACKEND'] = 'ffmpeg'
    
    if getattr(sys, 'frozen', False):
        # Application is frozen - set ffmpeg path for Qt
        ffmpeg_dir = sys._MEIPASS
        if 'PATH' in os.environ:
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']
        else:
            os.environ['PATH'] = ffmpeg_dir

def play_video(file_path):
    """
    Play a video file using the bundled or system ffmpeg binary.
    
    Args:
        file_path (str): Path to the video file to play
    """
    ffmpeg = get_ffmpeg_path()
    subprocess.run([ffmpeg, "-i", file_path]) 