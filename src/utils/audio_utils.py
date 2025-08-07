import sys
import os
from collections import OrderedDict
from threading import Lock
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect
from PyQt6.QtCore import QUrl, QObject, pyqtSignal, QTimer
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

# ----- Sound Effect Utilities (multiple overlapping sounds) -----

class SoundEffectPool:
    """
    Manages a pool of QSoundEffect instances for each sound file.
    This prevents lag from creating new instances and allows multiple
    overlapping plays of the same sound.
    """
    
    def __init__(self, max_instances_per_sound=5):
        self.pools = {}  # filename -> list of QSoundEffect instances
        self.max_instances = max_instances_per_sound
        self.lock = Lock()
        
    def get_effect(self, filename, audio_path):
        """
        Get an available sound effect instance from the pool.
        Creates new instances as needed up to max_instances.
        """
        with self.lock:
            if filename not in self.pools:
                self.pools[filename] = []
            
            pool = self.pools[filename]
            
            # Find an available (not playing) instance
            for effect in pool:
                if not effect.isPlaying():
                    return effect
            
            # If all instances are playing and we haven't reached max, create new one
            if len(pool) < self.max_instances:
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(audio_path))
                pool.append(effect)
                return effect
            
            # All instances are playing and we're at max - reuse the oldest one
            # This prevents unlimited memory growth but may cut off a sound
            if pool:
                return pool[0]
            
            return None
    
    def stop_all(self):
        """Stop all sound effects in all pools."""
        with self.lock:
            for pool in self.pools.values():
                for effect in pool:
                    if effect.isPlaying():
                        effect.stop()
    
    def clear(self):
        """Clear all pools and delete all QSoundEffect instances."""
        with self.lock:
            for pool in self.pools.values():
                for effect in pool:
                    if effect.isPlaying():
                        effect.stop()
                    effect.deleteLater()
            self.pools.clear()

# Global sound effect pool
_sound_effect_pool = SoundEffectPool(max_instances_per_sound=3)

# LRU cache for precached sound effects (first play)
_precache_order = OrderedDict()
_MAX_PRECACHE_SIZE = 50

# List of sound effects to precache at startup for optimal performance
# Includes all sound effects (excluding music files) from the audio directory
_PRECACHE_SOUND_EFFECTS = [
    # UI sound effects (title screen)
    "buttonhover.wav",
    "buttonclick.wav",
    
    # Startup sequence sounds
    "startup1of3.wav", 
    "startup2of3.wav",
    "startup3of3.wav",
    
    # Component interaction sounds
    "placecomponent.wav",
    "deletecomponent.wav",
    
    # Simulation control sounds
    "autocomplete.wav",
    "simstart.wav",
    "simend.wav",
    
    # Feedback sounds
    "successchime.wav",
    "failchime.wav"
]

def play_sound_effect(filename, volume=0.8):
    """
    Play a one-shot sound effect without interrupting other audio.
    Uses a pool-based system for optimal performance and resource management.

    Args:
        filename (str): The audio file name located in src/ui/assets/audio/useable
        volume (float): Volume level from 0.0 to 1.0 (default 0.8)

    Returns:
        bool: True if playback started, False otherwise
    """
    try:
        audio_path = resource_path(f"src/ui/assets/audio/useable/{filename}")
        if not os.path.exists(audio_path):
            print(f"SoundEffect Error: file not found: {audio_path}")
            return False

        # Get an available effect from the pool
        effect = _sound_effect_pool.get_effect(filename, audio_path)
        if effect is None:
            print(f"SoundEffect Error: could not get effect from pool for {filename}")
            return False
        
        # Update precache order for LRU tracking
        if filename in _precache_order:
            # Move to end (most recently used)
            _precache_order.move_to_end(filename)
        else:
            # Add to precache order
            _precache_order[filename] = True
            # Remove oldest if we exceed max size
            if len(_precache_order) > _MAX_PRECACHE_SIZE:
                oldest = next(iter(_precache_order))
                del _precache_order[oldest]

        # Set volume and play
        effect.setVolume(volume)
        effect.play()
        
        return True
    except Exception as e:
        print(f"SoundEffect Error: failed to play {filename}: {e}")
        return False

def stop_all_sound_effects():
    """Stop all currently playing sound effects."""
    _sound_effect_pool.stop_all()

def precache_sound_effects():
    """
    Precache commonly used sound effects to eliminate loading lag.
    Creates initial pool instances for frequently used sounds.
    This should be called during application startup.
    """
    print("AudioPlayer: Precaching sound effects...")
    
    precached_count = 0
    for filename in _PRECACHE_SOUND_EFFECTS:
        try:
            audio_path = resource_path(f"src/ui/assets/audio/useable/{filename}")
            if os.path.exists(audio_path):
                # Pre-create one instance in the pool for this sound
                # This loads the audio data into memory for faster first play
                effect = _sound_effect_pool.get_effect(filename, audio_path)
                if effect:
                    # Add to precache order
                    _precache_order[filename] = True
                    precached_count += 1
                    print(f"AudioPlayer: Precached {filename}")
            else:
                print(f"AudioPlayer: Warning - precache file not found: {filename}")
        except Exception as e:
            print(f"AudioPlayer: Error precaching {filename}: {e}")
    
    print(f"AudioPlayer: Precached {precached_count} sound effects")

def clear_sound_effect_cache():
    """Clear the sound effect pools and cache to free memory."""
    global _precache_order
    _sound_effect_pool.clear()
    _precache_order.clear()

def cleanup_audio():
    """
    Clean up the global audio player resources and clear the sound effect cache.
    """
    global _global_audio_player
    if _global_audio_player is not None:
        _global_audio_player.cleanup()
        _global_audio_player = None
    clear_sound_effect_cache()

# ----- Dedicated Sound Effect Play Functions (one function per WAV file) -----

from PyQt6.QtMultimedia import QSoundEffect  # re-import for frozen environments

def play_buttonhover(volume=0.8):
    '''Play buttonhover.wav'''
    try:
        if not hasattr(play_buttonhover, '_effect'):
            effect = QSoundEffect()
            audio_path = resource_path('src/ui/assets/audio/useable/buttonhover.wav')
            effect.setSource(QUrl.fromLocalFile(audio_path))
            play_buttonhover._effect = effect
        effect = play_buttonhover._effect
        effect.setVolume(volume)
        effect.play()
        return True
    except Exception as e:
        print('SoundEffect Error (buttonhover):', e)
        return False

def play_buttonclick(volume=0.8):
    '''Play buttonclick.wav'''
    try:
        if not hasattr(play_buttonclick, '_effect'):
            effect = QSoundEffect()
            audio_path = resource_path('src/ui/assets/audio/useable/buttonclick.wav')
            effect.setSource(QUrl.fromLocalFile(audio_path))
            play_buttonclick._effect = effect
        effect = play_buttonclick._effect
        effect.setVolume(volume)
        effect.play()
        return True
    except Exception as e:
        print('SoundEffect Error (buttonclick):', e)
        return False

def play_deletecomponent(volume=0.8):
    '''Play deletecomponent.wav'''
    try:
        if not hasattr(play_deletecomponent, '_effect'):
            effect = QSoundEffect()
            audio_path = resource_path('src/ui/assets/audio/useable/deletecomponent.wav')
            effect.setSource(QUrl.fromLocalFile(audio_path))
            play_deletecomponent._effect = effect
        effect = play_deletecomponent._effect
        effect.setVolume(volume)
        effect.play()
        return True
    except Exception as e:
        print('SoundEffect Error (deletecomponent):', e)
        return False

def play_placecomponent(volume=0.8):
    '''Play placecomponent.wav'''
    try:
        if not hasattr(play_placecomponent, '_effect'):
            effect = QSoundEffect()
            audio_path = resource_path('src/ui/assets/audio/useable/placecomponent.wav')
            effect.setSource(QUrl.fromLocalFile(audio_path))
            play_placecomponent._effect = effect
        effect = play_placecomponent._effect
        effect.setVolume(volume)
        effect.play()
        return True
    except Exception as e:
        print('SoundEffect Error (placecomponent):', e)
        return False

def play_successchime(volume=0.8):
    '''Play successchime.wav'''
    try:
        if not hasattr(play_successchime, '_effect'):
            effect = QSoundEffect()
            audio_path = resource_path('src/ui/assets/audio/useable/successchime.wav')
            effect.setSource(QUrl.fromLocalFile(audio_path))
            play_successchime._effect = effect
        effect = play_successchime._effect
        effect.setVolume(volume)
        effect.play()
        return True
    except Exception as e:
        print('SoundEffect Error (successchime):', e)
        return False

def play_failchime(volume=0.8):
    '''Play failchime.wav'''
    try:
        if not hasattr(play_failchime, '_effect'):
            effect = QSoundEffect()
            audio_path = resource_path('src/ui/assets/audio/useable/failchime.wav')
            effect.setSource(QUrl.fromLocalFile(audio_path))
            play_failchime._effect = effect
        effect = play_failchime._effect
        effect.setVolume(volume)
        effect.play()
        return True
    except Exception as e:
        print('SoundEffect Error (failchime):', e)
        return False

def precache_sound_effects():
    '''Preload all sound effects for low latency'''
    print('AudioPlayer: Precaching sound effects...')
    sounds = [
        play_buttonhover,
        play_buttonclick,
        play_deletecomponent,
        play_placecomponent,
        play_successchime,
        play_failchime,
    ]
    count = 0
    for func in sounds:
        try:
            func(volume=0.0)
            count += 1
        except Exception as e:
            print('AudioPlayer: Error precaching', func.__name__, e)
    print(f'AudioPlayer: Precached {count} sound effects')

def stop_all_sound_effects():
    '''Stop all currently playing sound effects'''
    for func in [
        play_buttonhover,
        play_buttonclick,
        play_deletecomponent,
        play_placecomponent,
        play_successchime,
        play_failchime,
    ]:
        if hasattr(func, '_effect'):
            eff = func._effect
            if eff.isPlaying():
                eff.stop()