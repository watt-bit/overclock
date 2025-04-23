from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import os

class AudioPlayer:
    """Utility class to manage audio playback"""
    
    def __init__(self):
        self.player = QMediaPlayer()
        self.is_playing = False
        self.is_looping = False
        self.timer = None
        
    def play(self, audio_file_path, loop=False):
        """
        Play an audio file
        
        Args:
            audio_file_path (str): Path to the audio file
            loop (bool): Whether to loop the audio
        """
        if not os.path.exists(audio_file_path):
            print(f"Audio file not found: {audio_file_path}")
            return False
        
        # Create media content from the file
        url = QUrl.fromLocalFile(audio_file_path)
        media = QMediaContent(url)
        
        # Set the media and play
        self.player.setMedia(media)
        self.is_looping = loop
        
        # Set up looping if requested
        if loop:
            # Connect to media status changed signal to handle looping
            self.player.mediaStatusChanged.connect(self._handle_media_status_changed)
        
        # Play the media
        self.player.play()
        self.is_playing = True
        return True
    
    def _handle_media_status_changed(self, status):
        """Handle media status changes for looping"""
        if status == QMediaPlayer.EndOfMedia and self.is_looping:
            self.player.setPosition(0)
            self.player.play()
    
    def stop(self):
        """Stop playback"""
        if self.is_playing:
            # Disconnect the signal to prevent memory leaks
            try:
                self.player.mediaStatusChanged.disconnect(self._handle_media_status_changed)
            except TypeError:
                # Signal was not connected
                pass
                
            self.player.stop()
            self.is_playing = False
            self.is_looping = False
    
    def set_volume(self, volume):
        """
        Set the volume level
        
        Args:
            volume (int): Volume level (0-100)
        """
        self.player.setVolume(volume) 