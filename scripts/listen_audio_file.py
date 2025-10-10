"""
Audio Waveform Player
---------------------

This tool loads a WAV file, displays its waveform in real time,
and lets you play/pause the audio with synchronized visualization.

Usage:
    python audio_waveform_player.py

    - When prompted, enter the path to a WAV file.
    - The waveform will be displayed in a matplotlib window.
    - Controls:
        * SPACE: toggle play/pause
        * Mouse click on waveform: seek to clicked position
        * Close the window: exit program

Requirements:
    pip install numpy matplotlib soundfile sounddevice

Author:
    Name: Zygimantas Jasiunas
    Affiliation: LASIGE - Faculty of Sciences of the University of Lisbon
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import soundfile as sf
import sounddevice as sd
import threading
import time
from datetime import datetime

class AudioWaveformPlayer:
    def __init__(self, wav_file):
        # Load the audio file
        self.audio_data, self.sample_rate = sf.read(wav_file)
        
        # Handle stereo audio by converting to mono
        if len(self.audio_data.shape) > 1:
            self.audio_data = np.mean(self.audio_data, axis=1)
        
        self.duration = len(self.audio_data) / self.sample_rate
        self.current_position = 0
        self.seek_offset = 0  # For handling seeks
        self.is_playing = False
        self.start_time = None
        
        # Set up the plot
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        
        # Downsample for visualization (keep max ~5000 points for smooth plotting)
        max_points = 5000
        if len(self.audio_data) > max_points:
            # Calculate step size for downsampling
            step = len(self.audio_data) // max_points
            self.display_audio = self.audio_data[::step]
            self.display_time = np.linspace(0, self.duration, len(self.display_audio))
        else:
            self.display_audio = self.audio_data
            self.display_time = np.linspace(0, self.duration, len(self.audio_data))
        
        # Plot the downsampled waveform
        self.ax.plot(self.display_time, self.display_audio, 'b-', alpha=0.7, linewidth=0.8)
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Amplitude')
        self.ax.set_title(f'Audio Waveform Player - Time: 0.00s / {self.duration:.2f}s')
        self.ax.grid(True, alpha=0.3)
        
        # Create the position line
        self.position_line = self.ax.axvline(x=0, color='red', linewidth=2, label='Current Position')
        self.ax.legend()
        
        # Set up the animation
        self.anim = None
        
    def play_audio(self):
        """Play the audio file"""
        try:
            # Calculate which part of audio to play based on current position
            start_sample = int(self.current_position * self.sample_rate)
            audio_to_play = self.audio_data[start_sample:]
            
            if len(audio_to_play) > 0:
                sd.play(audio_to_play, self.sample_rate)
                self.is_playing = True
                self.start_time = time.time()
                self.seek_offset = self.current_position
                print(f"Playing from {self.current_position:.2f}s")
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def stop_audio(self):
        """Stop the audio playback"""
        sd.stop()
        self.is_playing = False
        # Keep current position when pausing
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.current_position = min(self.seek_offset + elapsed, self.duration)
        print(f"Stopped at {self.current_position:.2f}s")
    
    def update_position(self, frame):
        """Update the position line based on playback time"""
        if self.is_playing and self.start_time:
            elapsed_time = time.time() - self.start_time
            self.current_position = min(elapsed_time + self.seek_offset, self.duration)
            
            # Stop when audio finishes
            if self.current_position >= self.duration:
                self.is_playing = False
                self.current_position = self.duration
                sd.stop()  # Ensure audio is stopped
        
        # Update the position line - only update x position
        self.position_line.set_xdata([self.current_position, self.current_position])
        
        return [self.position_line]
    
    def start_visualization(self):
        """Start the real-time visualization"""
        # Set up the animation with optimized settings
        self.anim = animation.FuncAnimation(
            self.fig, self.update_position, interval=50, blit=True, cache_frame_data=False
        )
        
        # Set up mouse click event for seeking
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Add a status display
        self.status_text = self.ax.text(0.02, 0.95, '', transform=self.ax.transAxes, 
                                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.tight_layout()
        plt.show()
    
    def on_click(self, event):
        """Handle mouse clicks for seeking"""
        if event.inaxes == self.ax and event.xdata is not None:
            was_playing = self.is_playing
            
            # Stop current playback
            self.stop_audio()
            
            # Set new position
            click_time = max(0, min(event.xdata, self.duration))
            self.current_position = click_time
            print(f"Seeking to {click_time:.2f}s")
            
            # Resume playing if it was playing before
            if was_playing:
                self.play_audio()

def main():
    # Replace with your WAV file path
    wav_file = input("Enter the path to your WAV file: ").strip()
    
    try:
        player = AudioWaveformPlayer(wav_file)
        
        print("Audio Waveform Player")
        print("Controls:")
        print("- Press SPACE to play/pause")
        print("- Click on the waveform to seek to that position")
        print("- Click on the waveform to seek to that position")
        print("- Close the window to exit")
        print(f"Audio length: {player.duration:.2f} seconds")
        print(f"Sample rate: {player.sample_rate} Hz")
        print(f"Visualization points: {len(player.display_audio)}")
        print(f"Original audio samples: {len(player.audio_data)}")
        print()
        # Set up keyboard controls
        def on_key(event):
            if event.key == ' ':  # Spacebar
                if player.is_playing:
                    player.stop_audio()
                else:
                    player.play_audio()
        
        player.fig.canvas.mpl_connect('key_press_event', on_key)
        
        # Start the visualization
        player.start_visualization()
        
    except FileNotFoundError:
        print("File not found. Please check the file path.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()