import sys
import os
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QObject, pyqtSignal
from src.utils.resource import resource_path

class AudioPlayer(QObject):
    """
    A utility class for playing audio files in the OVERCLOCK application.
    Provides progressive audio functionality with proper resource management.
    """
    
    # Signals for audio events
    playback_finished = pyqtSignal()
    playback_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create media player and audio output
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        
        # Connect audio output to media player
        self.media_player.setAudioOutput(self.audio_output)
        
        # Connect signals for monitoring playback
        self.media_player.mediaStatusChanged.connect(self._handle_media_status)
        self.media_player.errorOccurred.connect(self._handle_error)
        
        # Default volume (range 0.0 to 1.0)
        self.audio_output.setVolume(0.7)
        
        # Track current file for debugging
        self._current_file = None
        self._should_loop = False
    
    def play_audio_file(self, filename, loop=False):
        """
        Play an audio file from the assets/audio/useable directory.
        
        Args:
            filename (str): Name of the audio file (e.g., "TheAdventureBEGINS.wav")
            loop (bool): Whether to loop the audio when it reaches the end
        
        Returns:
            bool: True if playback started successfully, False otherwise
        """
        try:
            # Stop any currently playing audio
            self.stop()
            
            # Construct full path to audio file
            audio_path = resource_path(f"src/ui/assets/audio/useable/{filename}")
            
            # Check if file exists
            if not os.path.exists(audio_path):
                error_msg = f"Audio file not found: {audio_path}"
                print(f"AudioPlayer Error: {error_msg}")
                self.playback_error.emit(error_msg)
                return False
            
            # Set the audio source and start playback
            self._current_file = filename
            self._should_loop = loop
            audio_url = QUrl.fromLocalFile(audio_path)
            self.media_player.setSource(audio_url)
            self.media_player.play()
            
            loop_text = " (looping)" if loop else ""
            print(f"AudioPlayer: Started playing {filename}{loop_text}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to play audio file {filename}: {str(e)}"
            print(f"AudioPlayer Error: {error_msg}")
            self.playback_error.emit(error_msg)
            return False
    
    def stop(self):
        """Stop audio playback."""
        if self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.media_player.stop()
            if self._current_file:
                print(f"AudioPlayer: Stopped playing {self._current_file}")
                self._current_file = None
                self._should_loop = False
    
    def pause(self):
        """Pause audio playback."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            print(f"AudioPlayer: Paused {self._current_file}")
    
    def resume(self):
        """Resume audio playback."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
            print(f"AudioPlayer: Resumed {self._current_file}")
    
    def set_volume(self, volume):
        """
        Set the audio volume.
        
        Args:
            volume (float): Volume level from 0.0 (silent) to 1.0 (maximum)
        """
        volume = max(0.0, min(1.0, volume))  # Clamp to valid range
        self.audio_output.setVolume(volume)
        print(f"AudioPlayer: Set volume to {volume}")
    
    def get_volume(self):
        """Get the current audio volume."""
        return self.audio_output.volume()
    
    def is_playing(self):
        """Check if audio is currently playing."""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
    
    def is_paused(self):
        """Check if audio is currently paused."""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState
    
    def is_stopped(self):
        """Check if audio is stopped."""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState
    
    def cleanup(self):
        """Clean up audio resources."""
        self.stop()
        # Disconnect signals to prevent callbacks during cleanup
        try:
            self.media_player.mediaStatusChanged.disconnect()
            self.media_player.errorOccurred.disconnect()
        except TypeError:
            pass  # Signals may already be disconnected
    
    def _handle_media_status(self, status):
        """Handle media status changes."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self._should_loop and self._current_file:
                print(f"AudioPlayer: Looping {self._current_file}")
                # Restart the same file
                self.media_player.play()
            else:
                print(f"AudioPlayer: Finished playing {self._current_file}")
                self._current_file = None
                self._should_loop = False
                self.playback_finished.emit()
    
    def _handle_error(self, error, error_string):
        """Handle media player errors."""
        error_msg = f"Media player error for {self._current_file}: {error_string}"
        print(f"AudioPlayer Error: {error_msg}")
        self.playback_error.emit(error_msg)


# Global audio player instance for simple access across the application
_global_audio_player = None

def get_audio_player():
    """
    Get the global audio player instance.
    Creates one if it doesn't exist.
    
    Returns:
        AudioPlayer: The global audio player instance
    """
    global _global_audio_player
    if _global_audio_player is None:
        _global_audio_player = AudioPlayer()
    return _global_audio_player

def play_audio(filename, loop=False):
    """
    Convenience function to play an audio file using the global audio player.
    
    Args:
        filename (str): Name of the audio file to play
        loop (bool): Whether to loop the audio when it reaches the end
    
    Returns:
        bool: True if playback started successfully, False otherwise
    """
    return get_audio_player().play_audio_file(filename, loop)

def stop_audio():
    """Convenience function to stop audio playback using the global audio player."""
    get_audio_player().stop()

def cleanup_audio():
    """Clean up the global audio player resources."""
    global _global_audio_player
    if _global_audio_player is not None:
        _global_audio_player.cleanup()
        _global_audio_player = None