import os
import streamlit as st
from datetime import datetime
import base64
from pathlib import Path
import mimetypes

# Set page config for better display
st.set_page_config(
    page_title="Surveillance Video Dashboard",
    layout="wide"
)

# Constants
CAPTURE_DIR = '/home/pi/python_code/surveillance_footage'

def get_video_html(video_path):
    """
    Create an HTML5 video player for the given video path
    """
    # Get the video file name for display
    video_filename = os.path.basename(video_path)
    
    # Create a base64 data URI for the video
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
        video_b64 = base64.b64encode(video_bytes).decode()
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(video_path)
    if not mime_type:
        mime_type = 'video/mp4'  # Default to MP4 if type cannot be determined
    
    # HTML5 video player with controls
    video_html = f"""
        <video width="100%" controls autoplay muted>
            <source src="data:{mime_type};base64,{video_b64}" type="{mime_type}">
            Your browser does not support the video tag.
        </video>
        <p style="text-align: center; color: #666;">Playing: {video_filename}</p>
    """
    return video_html

def check_video_file(file_path):
    """
    Check if the file is a valid video file and accessible
    """
    try:
        if not os.path.exists(file_path):
            return False
        
        # Check file size
        if os.path.getsize(file_path) == 0:
            return False
            
        # Check mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type is not None and mime_type.startswith('video/')
    
    except Exception:
        return False

def get_video_details(file_path):
    """
    Get video file details
    """
    stats = os.stat(file_path)
    return {
        'size': f"{stats.st_size / (1024*1024):.2f} MB",
        'created': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
        'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }

def main():
    st.title("Surveillance Video Dashboard")
    
    # Check if directory exists
    if not os.path.exists(CAPTURE_DIR):
        st.error(f"Directory not found: {CAPTURE_DIR}")
        st.info("Please check your surveillance footage directory path.")
        return

    # Get available dates (folders)
    try:
        dates = [d for d in os.listdir(CAPTURE_DIR) 
                if os.path.isdir(os.path.join(CAPTURE_DIR, d))]
        dates.sort(reverse=True)
    except Exception as e:
        st.error(f"Error accessing directory: {str(e)}")
        return

    if not dates:
        st.warning("No surveillance footage available.")
        return

    # Create two columns for better layout
    col1, col2 = st.columns([1, 2])

    with col1:
        selected_date = st.selectbox("Select Date", dates)
        
        # Get videos for selected date
        video_dir = os.path.join(CAPTURE_DIR, selected_date)
        videos = [v for v in os.listdir(video_dir) 
                 if v.lower().endswith(('.mp4', '.avi', '.mov'))]
        videos.sort(reverse=True)

        if not videos:
            st.warning("No videos found for the selected date.")
            return

        selected_video = st.selectbox("Select Video", videos)

    with col2:
        if selected_video:
            video_path = os.path.join(video_dir, selected_video)
            
            if not check_video_file(video_path):
                st.error("Selected video file is invalid or corrupted.")
                return

            # Display video details
            details = get_video_details(video_path)
            st.write("Video Details:")
            st.write(f"- Size: {details['size']}")
            st.write(f"- Created: {details['created']}")
            st.write(f"- Modified: {details['modified']}")

            # Add a divider
            st.markdown("---")

            try:
                # Create a download button for the video
                with open(video_path, 'rb') as video_file:
                    st.download_button(
                        label="Download Video",
                        data=video_file,
                        file_name=selected_video,
                        mime="video/mp4"
                    )
                
                # Try the custom HTML5 video player first
                try:
                    video_html = get_video_html(video_path)
                    st.markdown(video_html, unsafe_allow_html=True)
                except Exception as e:
                    st.error("Error with HTML5 player, falling back to default player")
                    # Fallback to default Streamlit video player
                    st.video(video_path)
                
            except Exception as e:
                st.error(f"Error playing video: {str(e)}")
                st.info("Try downloading the video and playing it locally.")

            # Add video format information
            st.markdown("---")
            st.info("""
            Supported video formats:
            - MP4 (H.264 codec recommended)
            - AVI
            - MOV
            
            If you're having playback issues, try converting your videos to MP4 with H.264 encoding.
            """)

if __name__ == "__main__":
    main()
