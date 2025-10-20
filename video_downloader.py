import os
from PyQt5.QtCore import QThread, pyqtSignal

class VideoDownloaderThread(QThread):
    progress_signal = pyqtSignal(float, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, url, format_id, output_path, output_ext=None):
        super().__init__()
        self.url = url
        self.format_id = format_id
        self.output_path = output_path
        self.output_ext = output_ext  # Desired output extension (mp4, mp3, m4a, webm, mkv, etc.)
        
    def run(self):
        try:
            import yt_dlp
            
            def progress_hook(d):
                if d.get('status') == 'downloading':
                    try:
                        # Prefer exact byte counts when available
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                        
                        if total > 0:
                            percent = (downloaded / total) * 100
                        else:
                            # Fallback to percent string
                            p = d.get('_percent_str', '0%')
                            if p and '%' in p:
                                p = p.replace('%', '').strip()
                                percent = float(p)
                            else:
                                percent = 0.0
                        
                        # Get other info
                        eta = d.get('_eta_str', '')
                        speed = d.get('_speed_str', '')
                        
                        # Ensure percent is within range
                        percent = max(0.0, min(100.0, float(percent)))
                        
                        # Emit signal to update UI, force update every second
                        self.progress_signal.emit(percent, f"Kalan: {eta} | Hız: {speed}")
                    except Exception as e:
                        print(f"Progress update error: {str(e)}")
                elif d.get('status') == 'finished':
                    # Ensure UI shows 100% when download finishes
                    self.progress_signal.emit(100.0, "İndirme tamamlandı, işleniyor...")
            
            # Build format string
            format_str = self.format_id or 'best'

            # If user requested an audio-only output extension, ensure we request audio
            audio_exts = {'mp3', 'm4a', 'wav', 'ogg'}
            video_exts = {'mp4', 'webm', 'mkv'}
            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
            }

            # Parse the format string to understand what kind of media we're requesting
            is_video_request = 'video' in format_str or ('+' in format_str and not format_str.startswith('bestaudio'))
            is_audio_only_request = ('bestaudio' in format_str) and ('video' not in format_str) and ('+' not in format_str)
            
            print(f"Format string: {format_str}")
            print(f"Is video request: {is_video_request}")
            print(f"Is audio only: {is_audio_only_request}")
            
            # If output_ext provided, use it to decide merging/postprocessing
            if self.output_ext:
                out = self.output_ext.lower()
                
                # For video containers
                if out in video_exts:
                    # Force output format to be the selected container
                    ydl_opts['merge_output_format'] = out
                    
                    # If user requested something that looks like audio-only but selected video output,
                    # adjust the request to include video
                    if is_audio_only_request:
                        ydl_opts['format'] = f"bestvideo[ext={out}]+bestaudio/best"
                        print(f"Adjusting audio-only request to include video: {ydl_opts['format']}")
                
                # For audio containers
                elif out in audio_exts and is_audio_only_request:
                    # For audio-only output, configure FFmpeg to extract audio
                    if 'bestaudio' not in format_str and 'audio' not in format_str:
                        ydl_opts['format'] = 'bestaudio/best'
                    
                    # Configure audio extraction
                    if out == 'mp3':
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': out,
                        }]
                    
                    print(f"Configured for audio extraction to {out}")
                    
                # Handle edge case: video request with audio container
                elif out in audio_exts and is_video_request:
                    # Override to MP4 if trying to save video as audio format
                    ydl_opts['merge_output_format'] = 'mp4'
                    print("Warning: Attempted to save video as audio format. Defaulting to MP4.")
                
                print(f"Final ydl_opts: {ydl_opts}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)
                self.finished_signal.emit(filename)
                
        except Exception as e:
            self.error_signal.emit(str(e))


class InfoExtractorThread(QThread):
    info_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.info_signal.emit(info)
                
        except Exception as e:
            self.error_signal.emit(str(e))