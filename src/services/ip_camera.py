"""IP/WiFi camera discovery and connection utilities.

Why this design:
- Support both manual IP entry and automatic network discovery.
- Use RTSP and HTTP protocols for common IP camera standards.
- Provide non-blocking discovery to avoid UI freezes.
- Return camera URLs compatible with OpenCV VideoCapture.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from dataclasses import dataclass
from typing import List, Optional, Callable
from urllib.parse import urlparse

import cv2
import requests

# Building intelligence through code.

LOGGER = logging.getLogger("anomrecorder.ip_camera")

# Common RTSP ports
RTSP_PORTS = [554, 8554]

# Common HTTP/MJPEG ports  
HTTP_PORTS = [80, 8080, 8081]

# Timeout for connection attempts
CONNECTION_TIMEOUT = 3.0


@dataclass
class IPCamera:
    """Represents a discovered or manually configured IP camera."""
    name: str
    url: str
    protocol: str  # 'rtsp', 'http', 'mjpeg'
    ip: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    def get_opencv_url(self) -> str:
        """Generate OpenCV-compatible URL with credentials if provided."""
        if self.username and self.password:
            # Insert credentials into URL
            parsed = urlparse(self.url)
            if parsed.scheme in ('rtsp', 'http', 'https'):
                return f"{parsed.scheme}://{self.username}:{self.password}@{parsed.netloc}{parsed.path}"
        return self.url


def test_rtsp_connection(ip: str, port: int, username: str = "", password: str = "", 
                         path: str = "") -> Optional[str]:
    """Test RTSP connection to an IP camera.
    
    Args:
        ip: Camera IP address
        port: RTSP port (usually 554)
        username: Optional username
        password: Optional password  
        path: Optional RTSP path (e.g., /stream1)
        
    Returns:
        RTSP URL if successful, None otherwise
    """
    # Try common RTSP paths if none specified
    paths_to_try = [path] if path else [
        "", "/", "/stream1", "/stream", "/live", "/h264", "/0", "/1",
        "/cam/realmonitor", "/Streaming/Channels/101"
    ]
    
    for test_path in paths_to_try:
        if username and password:
            url = f"rtsp://{username}:{password}@{ip}:{port}{test_path}"
        else:
            url = f"rtsp://{ip}:{port}{test_path}"
            
        LOGGER.debug(f"Testing RTSP: {url}")
        
        try:
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to read a frame with timeout
            start = time.time()
            success = False
            while time.time() - start < CONNECTION_TIMEOUT:
                ret, _ = cap.read()
                if ret:
                    success = True
                    break
                time.sleep(0.1)
                
            cap.release()
            
            if success:
                LOGGER.info(f"RTSP connection successful: {ip}:{port}{test_path}")
                return url
                
        except Exception as e:
            LOGGER.debug(f"RTSP test failed: {e}")
            continue
            
    return None


def test_http_mjpeg(ip: str, port: int, username: str = "", password: str = "",
                    path: str = "") -> Optional[str]:
    """Test HTTP/MJPEG connection to an IP camera.
    
    Args:
        ip: Camera IP address
        port: HTTP port (usually 80, 8080, 8081)
        username: Optional username
        password: Optional password
        path: Optional HTTP path
        
    Returns:
        HTTP URL if successful, None otherwise
    """
    # Try common HTTP/MJPEG paths if none specified
    paths_to_try = [path] if path else [
        "/video", "/video.mjpg", "/mjpeg", "/mjpg/video.mjpg",
        "/cgi-bin/mjpg/video.cgi", "/videostream.cgi"
    ]
    
    for test_path in paths_to_try:
        url = f"http://{ip}:{port}{test_path}"
        
        LOGGER.debug(f"Testing HTTP: {url}")
        
        try:
            auth = None
            if username and password:
                from requests.auth import HTTPBasicAuth
                auth = HTTPBasicAuth(username, password)
                
            response = requests.get(url, auth=auth, timeout=CONNECTION_TIMEOUT, stream=True)
            
            # Accept both 200 OK and 206 Partial Content (common for IP camera streaming)
            if response.status_code in (200, 206):
                # Test if OpenCV can open it
                if username and password:
                    opencv_url = f"http://{username}:{password}@{ip}:{port}{test_path}"
                else:
                    opencv_url = url
                    
                cap = cv2.VideoCapture(opencv_url)
                ret, _ = cap.read()
                cap.release()
                
                if ret:
                    LOGGER.info(f"HTTP connection successful: {ip}:{port}{test_path}")
                    return opencv_url
                    
        except Exception as e:
            LOGGER.debug(f"HTTP test failed: {e}")
            continue
            
    return None


def scan_ip_for_camera(ip: str, username: str = "", password: str = "") -> Optional[IPCamera]:
    """Scan a single IP address for camera services.
    
    Args:
        ip: IP address to scan
        username: Optional username for authentication
        password: Optional password for authentication
        
    Returns:
        IPCamera object if a camera is found, None otherwise
    """
    LOGGER.debug(f"Scanning {ip} for cameras...")
    
    # Try RTSP first (most common for IP cameras)
    for port in RTSP_PORTS:
        url = test_rtsp_connection(ip, port, username, password)
        if url:
            return IPCamera(
                name=f"Camera at {ip}:{port}",
                url=url,
                protocol="rtsp",
                ip=ip,
                port=port,
                username=username if username else None,
                password=password if password else None
            )
    
    # Try HTTP/MJPEG
    for port in HTTP_PORTS:
        url = test_http_mjpeg(ip, port, username, password)
        if url:
            return IPCamera(
                name=f"Camera at {ip}:{port}",
                url=url,
                protocol="mjpeg",
                ip=ip,
                port=port,
                username=username if username else None,
                password=password if password else None
            )
    
    return None


def get_local_network_range() -> List[str]:
    """Get the local network IP range for scanning.
    
    Returns:
        List of IP addresses in the local subnet
    """
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Generate subnet range (assumes /24 network)
        parts = local_ip.split('.')
        subnet = '.'.join(parts[:3])
        
        # Return range of IPs (skip .0 and .255)
        return [f"{subnet}.{i}" for i in range(1, 255)]
        
    except Exception as e:
        LOGGER.error(f"Failed to get network range: {e}")
        return []


class CameraScanner:
    """Asynchronous IP camera scanner for network discovery."""
    
    def __init__(self):
        self.is_scanning = False
        self.found_cameras: List[IPCamera] = []
        self.scan_thread: Optional[threading.Thread] = None
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        
    def start_scan(self, 
                   username: str = "", 
                   password: str = "",
                   progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Start scanning the local network for cameras.
        
        Args:
            username: Optional username for camera authentication
            password: Optional password for camera authentication
            progress_callback: Optional callback(current, total) for progress updates
        """
        if self.is_scanning:
            LOGGER.warning("Scan already in progress")
            return
            
        self.found_cameras = []
        self.is_scanning = True
        self.progress_callback = progress_callback
        
        def scan_worker():
            ips = get_local_network_range()
            total = len(ips)
            
            LOGGER.info(f"Starting network scan of {total} addresses...")
            
            for i, ip in enumerate(ips):
                if not self.is_scanning:
                    break
                    
                camera = scan_ip_for_camera(ip, username, password)
                if camera:
                    self.found_cameras.append(camera)
                    LOGGER.info(f"Found camera: {camera.name}")
                    
                if self.progress_callback:
                    try:
                        self.progress_callback(i + 1, total)
                    except Exception as e:
                        LOGGER.error(f"Progress callback error: {e}")
                        
            self.is_scanning = False
            LOGGER.info(f"Scan complete. Found {len(self.found_cameras)} cameras.")
            
        self.scan_thread = threading.Thread(target=scan_worker, daemon=True)
        self.scan_thread.start()
        
    def stop_scan(self) -> None:
        """Stop an ongoing scan."""
        self.is_scanning = False
        if self.scan_thread:
            self.scan_thread.join(timeout=1.0)
            
    def get_found_cameras(self) -> List[IPCamera]:
        """Get list of cameras found during scan."""
        return self.found_cameras.copy()


def create_manual_camera(ip: str, port: int, protocol: str = "rtsp",
                        username: str = "", password: str = "",
                        path: str = "") -> Optional[IPCamera]:
    """Create an IP camera connection from manual configuration.
    
    Args:
        ip: Camera IP address
        port: Camera port
        protocol: Protocol type ('rtsp' or 'http')
        username: Optional username
        password: Optional password
        path: Optional URL path
        
    Returns:
        IPCamera object if connection successful, None otherwise
    """
    if protocol.lower() == "rtsp":
        url = test_rtsp_connection(ip, port, username, password, path)
        if url:
            return IPCamera(
                name=f"Camera at {ip}:{port}",
                url=url,
                protocol="rtsp",
                ip=ip,
                port=port,
                username=username if username else None,
                password=password if password else None
            )
    elif protocol.lower() in ("http", "mjpeg"):
        url = test_http_mjpeg(ip, port, username, password, path)
        if url:
            return IPCamera(
                name=f"Camera at {ip}:{port}",
                url=url,
                protocol="mjpeg",
                ip=ip,
                port=port,
                username=username if username else None,
                password=password if password else None
            )
            
    return None


__all__ = ["IPCamera", "CameraScanner", "create_manual_camera", "scan_ip_for_camera"]
