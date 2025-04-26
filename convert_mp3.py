import os
import subprocess
import argparse
from pathlib import Path

def convert_webm_to_mp3(input_file, output_file=None, bitrate="192k"):
    """
    Convert WebM file to MP3 using ffmpeg.
    
    Args:
        input_file (str): Path to the input WebM file
        output_file (str, optional): Path to the output MP3 file. If not provided, will use the same name as input with .mp3 extension
        bitrate (str, optional): Audio bitrate for the output MP3 file. Default is "192k"
    
    Returns:
        str: Path to the output MP3 file
    """
    # Check if input file exists
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found")
    
    # Create output file path if not provided
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".mp3"
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Run ffmpeg command
    try:
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-vn",  # No video
            "-ab", bitrate,
            "-ar", "44100",  # Audio sampling frequency
            "-y",  # Overwrite output files
            output_file
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Successfully converted '{input_file}' to '{output_file}'")
        return output_file
    
    except subprocess.CalledProcessError as e:
        print(f"Error converting file: {e.stderr.decode() if e.stderr else str(e)}")
        raise
