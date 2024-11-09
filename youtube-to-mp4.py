import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import yt_dlp
import humanize

# Global variables
available_formats = []
progress_bar = None
size_label = None

def fetch_formats(url):
    global available_formats
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'youtube_include_dash_manifest': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            available_formats = []
            for format in info['formats']:
                if 'height' in format and format['height'] is not None and format['ext'] == 'mp4':
                    resolution = f"{format['height']}p"
                    filesize = format.get('filesize', None)
                    if filesize is not None:
                        filesize = int(filesize)
                    available_formats.append({
                        'resolution': resolution,
                        'format_id': format['format_id'],
                        'filesize': filesize
                    })

            available_formats = sorted(
                list({v['resolution']:v for v in available_formats}.values()),
                key=lambda x: int(x['resolution'][:-1]),
                reverse=True
            )

            if not available_formats:
                messagebox.showerror("Error", "No suitable MP4 formats found!")
                return

            format_combobox['values'] = [f"{fmt['resolution']} ({humanize.naturalsize(fmt['filesize']) if fmt['filesize'] else 'Unknown size'})" for fmt in available_formats]
            format_combobox.current(0)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch formats: {str(e)}")

def download_progress_hook(d):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        if total_bytes > 0:
            percent = (downloaded_bytes / total_bytes) * 100
            progress_bar['value'] = percent
            size_label.config(text=f"Downloaded: {humanize.naturalsize(downloaded_bytes)} / {humanize.naturalsize(total_bytes)}")
            app.update_idletasks()

def download_video(url, output_path, format_id):
    ydl_opts = {
        'format': f'{format_id}+bestaudio[ext=m4a]/best[ext=m4a]',
        'outtmpl': output_path + '/%(title)s.mp4',
        'merge_output_format': 'mp4',
        'progress_hooks': [download_progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        messagebox.showinfo("Success", "Download completed!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download video: {str(e)}")
    finally:
        progress_bar['value'] = 0
        size_label.config(text="")

def start_download():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    if not available_formats:
        messagebox.showerror("Error", "No formats available. Please fetch formats first.")
        return

    selected_resolution = format_combobox.get().split()[0]
    format_id = next((fmt['format_id'] for fmt in available_formats if fmt['resolution'] == selected_resolution), None)
    if not format_id:
        messagebox.showerror("Error", "Failed to find the format ID for the selected resolution.")
        return

    output_path = filedialog.askdirectory()
    if not output_path:
        messagebox.showerror("Error", "Please select a download folder")
        return

    threading.Thread(target=download_video, args=(url, output_path, format_id), daemon=True).start()

def fetch_formats_clicked():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return
    threading.Thread(target=fetch_formats, args=(url,), daemon=True).start()

app = tk.Tk()
app.title("YouTube to MP4 Converter with Resolution Options")
app.geometry('400x400')

tk.Label(app, text="YouTube URL:").pack(pady=10)
url_entry = tk.Entry(app, width=50)
url_entry.pack(pady=5)

fetch_button = tk.Button(app, text="Fetch Available Formats", command=fetch_formats_clicked)
fetch_button.pack(pady=10)

tk.Label(app, text="Select Resolution:").pack(pady=5)
format_combobox = ttk.Combobox(app, state="readonly", width=40)
format_combobox.pack(pady=5)

download_button = tk.Button(app, text="Download MP4", command=start_download)
download_button.pack(pady=20)

progress_bar = ttk.Progressbar(app, orient='horizontal', length=300, mode='determinate')
progress_bar.pack(pady=10)

size_label = tk.Label(app, text="")
size_label.pack(pady=5)

app.mainloop()
