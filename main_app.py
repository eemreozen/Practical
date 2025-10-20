import os
import re
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog,
                           QProgressBar, QMessageBox, QSizePolicy, QApplication)
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QPixmap, QImage
from video_downloader import VideoDownloaderThread, InfoExtractorThread

class YouTubeConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Practical YouTube Video Converter")
        self.setMinimumSize(800, 600)
        
        self.video_info = None
        self.current_formats = []
        self.available_formats = {}  # Will store all available formats by resolution
        self.selected_format_id = "best"  # Default format
        
        self.init_ui()
        
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # URL input section
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.fetch_btn = QPushButton("Önizle")
        self.fetch_btn.clicked.connect(self.fetch_video_info)
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.fetch_btn)
        
        # Video preview section
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.thumbnail_label.setMinimumHeight(360)
        self.thumbnail_label.setStyleSheet("background-color: #f0f0f0;")
        
        # Video information
        info_layout = QHBoxLayout()
        self.video_title_label = QLabel("Başlık: ")
        self.video_duration_label = QLabel("Süre: ")
        info_layout.addWidget(self.video_title_label)
        info_layout.addWidget(self.video_duration_label)
        
        # Format selection - redesigned for clarity
        format_layout = QVBoxLayout()
        
        # Media type selection (first option to choose)
        media_type_layout = QHBoxLayout()
        media_type_label = QLabel("İndirme Tipi:")
        self.media_type_combo = QComboBox()
        self.media_type_combo.addItems(["Ses ve Video", "Sadece Video", "Sadece Ses"])
        self.media_type_combo.currentIndexChanged.connect(self.update_media_type)
        media_type_layout.addWidget(media_type_label)
        media_type_layout.addWidget(self.media_type_combo)
        
        # File format selection
        format_type_layout = QHBoxLayout()
        format_type_label = QLabel("Dosya Formatı:")
        self.format_type_combo = QComboBox()
        # Will be populated based on media type selection
        self.format_type_combo.currentIndexChanged.connect(self.update_available_formats)
        self.format_type_combo.setEnabled(False)
        format_type_layout.addWidget(format_type_label)
        format_type_layout.addWidget(self.format_type_combo)
        
        # Resolution selection
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Çözünürlük:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.setEnabled(False)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        
        # Download button
        button_layout = QHBoxLayout()
        self.download_btn = QPushButton("İndir")
        self.download_btn.clicked.connect(self.download_video)
        self.download_btn.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(self.download_btn)
        
        # Add all format selection components
        format_layout.addLayout(media_type_layout)
        format_layout.addLayout(format_type_layout)
        format_layout.addLayout(resolution_layout)
        format_layout.addLayout(button_layout)
        
        # Progress bar
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.eta_label = QLabel("")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.eta_label)
        
        # Add all components to main layout
        main_layout.addLayout(url_layout)
        main_layout.addWidget(self.thumbnail_label)
        main_layout.addLayout(info_layout)
        main_layout.addLayout(format_layout)
        main_layout.addLayout(progress_layout)
        
        # Set main widget
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def fetch_video_info(self):
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir YouTube URL'si girin.")
            return
            
        if not re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', url):
            QMessageBox.warning(self, "Uyarı", "Geçersiz YouTube URL'si.")
            return
            
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Yükleniyor...")
        
        # Reset UI elements when fetching a new video
        self.progress_bar.setValue(0)
        self.eta_label.setText("")
        self.thumbnail_label.clear()
        self.thumbnail_label.setText("Yükleniyor...")
        self.video_title_label.setText("Başlık: ")
        self.video_duration_label.setText("Süre: ")
        self.format_type_combo.clear()
        self.resolution_combo.clear()
        self.download_btn.setEnabled(False)
        
        self.info_thread = InfoExtractorThread(url)
        self.info_thread.info_signal.connect(self.handle_video_info)
        self.info_thread.error_signal.connect(self.handle_error)
        self.info_thread.start()
        
    def handle_video_info(self, info):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Önizle")
        self.download_btn.setEnabled(True)
        
        self.video_info = info
        
        # Show video title and duration
        title = info.get('title', 'Bilinmeyen Başlık')
        duration = info.get('duration', 0)
        mins, secs = divmod(duration, 60)
        hours, mins = divmod(mins, 60)
        
        duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours else f"{mins:02d}:{secs:02d}"
        
        self.video_title_label.setText(f"Başlık: {title}")
        self.video_duration_label.setText(f"Süre: {duration_str}")
        
        # Reset format selection to defaults - enable media type selection
        self.media_type_combo.setCurrentIndex(0)  # Default to "Ses ve Video"
        
        # Update available formats based on media type selection
        self.update_media_type()
        
        # Load thumbnail
        self.load_thumbnail(info)
        
    def load_thumbnail(self, info):
        """Load and display the video thumbnail"""
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            try:
                import urllib.request
                data = urllib.request.urlopen(thumbnail_url).read()
                image = QImage()
                image.loadFromData(data)
                
                # Scale the image to fit the label while maintaining aspect ratio
                pixmap = QPixmap.fromImage(image)
                pixmap = pixmap.scaled(
                    self.thumbnail_label.width(), 
                    self.thumbnail_label.height(),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                self.thumbnail_label.setPixmap(pixmap)
                
            except Exception as e:
                print(f"Error loading thumbnail: {str(e)}")
                self.thumbnail_label.setText("Thumbnail yüklenemedi")
        
    def handle_error(self, error_msg):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Önizle")
        QMessageBox.critical(self, "Hata", f"Hata oluştu: {error_msg}")
        
    def download_video(self):
        if not self.video_info:
            QMessageBox.warning(self, "Uyarı", "Önce bir video önizleyin.")
            return
            
        # Get format settings
        media_type = self.media_type_combo.currentText()
        format_type = self.format_type_combo.currentText()
        url = self.url_input.text().strip()
        
        # Get selected resolution/quality
        selected_option = self.resolution_combo.currentText()
        
        # Create summary of selected options for confirmation dialog
        format_summary = f"Dosya formatı: {format_type}"
        
        if media_type == "Sadece Ses":
            if selected_option == "Otomatik (En İyi)":
                format_summary = f"Yalnızca ses indirilecek (En yüksek kalitede {format_type} formatında)"
            else:
                format_summary = f"Yalnızca ses indirilecek ({selected_option}, {format_type} formatında)"
        else:
            if selected_option == "Otomatik (En İyi)" or selected_option == "En İyi Kalite":
                format_summary += f", En yüksek çözünürlükte"
            else:
                format_summary += f", Çözünürlük: {selected_option}"
                
            if media_type == "Sadece Video":
                format_summary += ", Ses olmadan"
            else:
                format_summary += ", Ses ile birlikte"
            
        # Add note about format if needed
        has_warning = ""
        if media_type == "Sadece Video":
            has_warning = "\n\nNot: Sadece video seçeneği seçildi. İndirilen dosyada ses olmayacaktır."
        
        proceed = QMessageBox.question(
            self,
            "İndirme Onayı",
            f"Seçilen ayarlar:\n{format_summary}{has_warning}\n\nİndirme işlemi başlatılsın mı?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if proceed != QMessageBox.Yes:
            return
            
        # Ask for save directory
        output_path = QFileDialog.getExistingDirectory(
            self, "İndirme Klasörünü Seçin", 
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        if not output_path:
            return
            
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.eta_label.setText("")
        
        # Get the format ID based on user selections
        format_id = self.selected_format_id
        # Determine desired output extension from selected file format
        selected_container = self.format_type_combo.currentText().lower()
        # Map some user-friendly names to actual extensions
        container_map = {
            'mp4': 'mp4', 'webm': 'webm', 'mkv': 'mkv',
            'mp3': 'mp3', 'm4a': 'm4a', 'wav': 'wav', 'ogg': 'ogg'
        }
        output_ext = container_map.get(selected_container, None)

        # MP3 gibi ses formatları için, sadece ses seçilmişse output_ext kullan
        # Aksi halde ses ve video birlikte seçilmişse, video formatını kullan
        if media_type == "Ses ve Video" and output_ext in ["mp3", "m4a", "wav", "ogg"]:
            # Ses formatı seçilmiş ama ses ve video birlikte isteniyor, video formatına çevir
            if format_type.upper() in ["MP3", "M4A", "WAV", "OGG"]:
                output_ext = "mp4"  # Varsayılan olarak MP4'e çevir
        
        print(f"İndiriliyor: Format ID={format_id}, Output Format={output_ext}, Media Type={media_type}")
                
        # Start download thread (pass desired output extension)
        self.download_thread = VideoDownloaderThread(url, format_id, output_path, output_ext=output_ext)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.handle_error)
        self.download_thread.start()
        
    def update_progress(self, percent, info_text):
        # Eğer hala açık bir indirme penceremiz varsa güncelle
        try:
            if not self.isVisible():
                return
                
            # Yüzde değerini ilerleme çubuğuna ayarla (0-100 arası)
            try:
                percent_int = min(int(percent), 100)  # 100'den büyük değerleri kırpma
                if percent_int >= 0:  # Sadece geçerli değerleri göster
                    self.progress_bar.setValue(percent_int)
            except:
                pass
                
            # İndirme hızı ve kalan süre bilgisini göster
            if info_text:
                self.eta_label.setText(info_text)
                
            # UI'ın güncellenmesini zorla
            QApplication.processEvents()
        except Exception as e:
            print(f"Progress update UI error: {str(e)}")
        
    def download_finished(self, filename):
        self.download_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.eta_label.setText("")
        QMessageBox.information(self, "İndirme Tamamlandı", 
                              f"Video başarıyla indirildi:\n{filename}")
                              
    def update_media_type(self):
        """Update format options based on media type selection (audio, video, or both)"""
        if not self.video_info:
            return
            
        media_type = self.media_type_combo.currentText()
        self.format_type_combo.clear()
        self.format_type_combo.setEnabled(True)
        
        # Enable/disable resolution combo based on media type
        show_resolution = media_type != "Sadece Ses"
        self.resolution_combo.setEnabled(show_resolution)
        
        # Populate format types based on media type
        if media_type == "Sadece Ses":
            self.format_type_combo.addItems(["MP3", "M4A", "WAV", "OGG"])
            self.selected_format_id = "bestaudio"
            self.resolution_combo.clear()
        elif media_type == "Sadece Video":
            self.format_type_combo.addItems(["MP4", "WebM", "MKV"])
        else:  # Ses ve Video
            self.format_type_combo.addItems(["MP4", "WebM", "MKV"])
            
        # Update formats based on new selection
        self.update_available_formats()
    
    def update_available_formats(self):
        """Update available resolutions based on selected format type and media type"""
        if not self.video_info:
            return
            
        selected_format = self.format_type_combo.currentText().lower()
        media_type = self.media_type_combo.currentText()
        
        self.resolution_combo.clear()
        self.available_formats = {}
        
        # "Otomatik" seçeneğini her zaman ekle
        self.resolution_combo.addItem("Otomatik (En İyi)")
        
        # For audio only
        if media_type == "Sadece Ses":
            self.resolution_combo.setEnabled(True)  # Enable to show audio qualities
            
            # Set format ID based on selected audio format
            audio_format = selected_format.lower()
            if audio_format == "mp3":
                self.selected_format_id = "bestaudio[ext=mp3]/bestaudio/best"
            elif audio_format == "m4a":
                self.selected_format_id = "bestaudio[ext=m4a]/bestaudio/best"
            elif audio_format == "wav":
                self.selected_format_id = "bestaudio[ext=wav]/bestaudio/best"
            elif audio_format == "ogg":
                self.selected_format_id = "bestaudio[ext=ogg]/bestaudio/best"
            else:
                self.selected_format_id = "bestaudio"
                
            # Kullanılabilir ses kalitelerini ekle
            audio_formats = []
            
            for f in self.video_info.get('formats', []):
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':  # Sadece ses içeren formatlar
                    audio_quality = f.get('abr', 0) or f.get('tbr', 0)  # Bit rate
                    format_id = f.get('format_id', '')
                    ext = f.get('ext', '').lower()
                    format_note = f.get('format_note', '')
                    
                    # Sadece seçilen formatta ses dosyalarını göster
                    if selected_format.lower() in ['mp3', 'm4a', 'wav', 'ogg']:
                        # Ses formatı dönüştürülebilir olduğundan hepsini göster
                        pass
                    elif ext != selected_format.lower():
                        continue
                    
                    if audio_quality > 0:
                        display_name = f"{int(audio_quality)}kbps"
                        if format_note:
                            display_name += f" ({format_note})"
                        
                        audio_formats.append({
                            'format_id': format_id,
                            'display_name': display_name,
                            'quality': audio_quality
                        })
            
            # Ses kalitelerine göre sırala (yüksekten düşüğe)
            audio_formats.sort(key=lambda x: x['quality'], reverse=True)
            
            # Combobox'a ekle
            for fmt in audio_formats:
                self.resolution_combo.addItem(fmt['display_name'])
                self.available_formats[fmt['display_name']] = {'format_id': fmt['format_id'], 'has_audio': True}
            
            return
            
        # For video formats
        video_formats = []
        
        for f in self.video_info.get('formats', []):
            ext = f.get('ext', '').lower()
            format_id = f.get('format_id', '')
            resolution = f.get('resolution', 'Unknown')
            fps = f.get('fps', 0)
            has_video = f.get('vcodec', '') != 'none'
            has_audio = f.get('acodec', '') != 'none'
            
            # Sadece seçilen formatta olanları göster
            if ext != selected_format.lower():
                continue
            
            # Medya tipine göre filtrele
            if media_type == "Sadece Video" and has_audio:
                continue
            elif media_type == "Ses ve Video" and not has_video:
                continue
                
            # Video formatlarını ekle
            if has_video and resolution != 'Unknown':
                display_name = resolution
                if fps:
                    display_name += f" {fps}fps"
                
                # Çözünürlük değerini güvenli bir şekilde dönüştür
                resolution_int = 0
                try:
                    if 'p' in resolution:
                        resolution_int = int(resolution.replace('p', ''))
                    elif 'x' in resolution:
                        # Format: 1280x720 şeklindeyse
                        height = resolution.split('x')[1]
                        resolution_int = int(height)
                    else:
                        resolution_int = 0
                except ValueError:
                    resolution_int = 0
                
                video_formats.append({
                    'format_id': format_id,
                    'display_name': display_name,
                    'resolution_int': resolution_int,
                    'fps': fps,
                    'has_audio': has_audio
                })
        
        # Çözünürlük ve FPS'e göre sırala (en yüksek çözünürlük ve FPS önce)
        video_formats.sort(key=lambda x: (x['resolution_int'], x['fps']), reverse=True)
        
        # Combobox'a ekle
        for fmt in video_formats:
            self.resolution_combo.addItem(fmt['display_name'])
            self.available_formats[fmt['display_name']] = {'format_id': fmt['format_id'], 'has_audio': fmt.get('has_audio', False)}
        
        # Eğer hiç format yoksa, bir varsayılan değer ekle
        if not video_formats and media_type != "Sadece Ses":
            self.resolution_combo.addItem("En İyi Kalite")
            
        # Connect resolution change handler
        self.resolution_combo.currentIndexChanged.connect(self.on_resolution_change)
        
        # Initialize with first option
        self.on_resolution_change()
        
        # Tek seferlik bağlantı ve başlatma yeterli
        try:
            # Önce mevcut bağlantıyı kaldır (eğer varsa)
            try:
                self.resolution_combo.currentIndexChanged.disconnect(self.on_resolution_change)
            except:
                pass
            
            # Connect resolution change handler
            self.resolution_combo.currentIndexChanged.connect(self.on_resolution_change)
            
            # Initialize with first option
            self.on_resolution_change()
        except Exception as e:
            print(f"Resolution combo setup error: {str(e)}")
    
    def on_resolution_change(self):
        """Handle resolution change"""
        if not self.video_info:
            return
        
        try:
            media_type = self.media_type_combo.currentText()
            selected_format = self.format_type_combo.currentText().lower()
            selected_resolution = self.resolution_combo.currentText()
            
            # Handle automatic option
            if selected_resolution == "Otomatik (En İyi)" or selected_resolution == "En İyi Kalite":
                if media_type == "Sadece Ses":
                    self.selected_format_id = f"bestaudio[ext={selected_format}]/bestaudio/best"
                elif media_type == "Sadece Video":
                    self.selected_format_id = f"bestvideo[ext={selected_format}]/best"
                else:  # Ses ve Video
                    self.selected_format_id = f"best[ext={selected_format}]/best"
                return
            
            # Check if the selected resolution/quality is in our available formats
            if selected_resolution in self.available_formats:
                format_data = self.available_formats[selected_resolution]
                
                # Emin olmak için format_id'yi doğru şekilde alıyoruz
                if isinstance(format_data, dict) and 'format_id' in format_data:
                    format_id = format_data['format_id']
                else:
                    # Eski yapıyla uyumluluk için
                    format_id = format_data
                
                # Adjust format ID based on media type
                if media_type == "Sadece Ses":
                    self.selected_format_id = format_id
                elif media_type == "Sadece Video":
                    self.selected_format_id = format_id
                else:  # Ses ve Video
                    self.selected_format_id = f"{format_id}+bestaudio/best"
            else:
                # Fallback to best
                if media_type == "Sadece Ses":
                    self.selected_format_id = f"bestaudio[ext={selected_format}]/bestaudio/best"
                elif media_type == "Sadece Video":
                    self.selected_format_id = f"bestvideo[ext={selected_format}]/best"
                else:  # Ses ve Video
                    self.selected_format_id = f"best[ext={selected_format}]/best"
        except Exception as e:
            print(f"Resolution change error: {str(e)}")
            # Hata durumunda güvenli bir varsayılan değer
            self.selected_format_id = "best"
    
    def resizeEvent(self, event):
        # Rescale thumbnail if it exists
        if hasattr(self, 'thumbnail_label') and self.thumbnail_label.pixmap() is not None:
            # Get original pixmap from thumbnail_label
            current_pixmap = self.thumbnail_label.pixmap()
            if current_pixmap and not current_pixmap.isNull():
                # Scale the pixmap to the new size while maintaining aspect ratio
                scaled_pixmap = current_pixmap.scaled(
                    self.thumbnail_label.width(), 
                    self.thumbnail_label.height(),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
        
        # Call parent's resizeEvent
        super().resizeEvent(event)