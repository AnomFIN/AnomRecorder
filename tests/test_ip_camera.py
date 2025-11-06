"""Tests for IP camera discovery and connection."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.ip_camera import (
    IPCamera,
    CameraScanner,
    create_manual_camera,
    scan_ip_for_camera,
    get_local_network_range,
)


def test_ip_camera_creation():
    """Test IPCamera dataclass creation."""
    camera = IPCamera(
        name="Test Camera",
        url="rtsp://192.168.1.100:554/stream",
        protocol="rtsp",
        ip="192.168.1.100",
        port=554,
        username="admin",
        password="password"
    )
    
    assert camera.name == "Test Camera"
    assert camera.ip == "192.168.1.100"
    assert camera.port == 554
    assert camera.protocol == "rtsp"


def test_ip_camera_opencv_url_with_credentials():
    """Test URL generation with credentials."""
    camera = IPCamera(
        name="Test Camera",
        url="rtsp://192.168.1.100:554/stream",
        protocol="rtsp",
        ip="192.168.1.100",
        port=554,
        username="admin",
        password="password"
    )
    
    opencv_url = camera.get_opencv_url()
    assert "admin:password@" in opencv_url
    assert "192.168.1.100" in opencv_url


def test_ip_camera_opencv_url_without_credentials():
    """Test URL generation without credentials."""
    camera = IPCamera(
        name="Test Camera",
        url="rtsp://192.168.1.100:554/stream",
        protocol="rtsp",
        ip="192.168.1.100",
        port=554
    )
    
    opencv_url = camera.get_opencv_url()
    assert opencv_url == "rtsp://192.168.1.100:554/stream"


def test_get_local_network_range():
    """Test local network range generation."""
    with patch('socket.socket') as mock_socket:
        mock_instance = Mock()
        mock_instance.getsockname.return_value = ('192.168.1.10', 0)
        mock_socket.return_value = mock_instance
        
        ips = get_local_network_range()
        
        assert len(ips) == 254  # 1-254
        assert "192.168.1.1" in ips
        assert "192.168.1.254" in ips
        assert "192.168.1.0" not in ips
        assert "192.168.1.255" not in ips


def test_camera_scanner_initialization():
    """Test CameraScanner initialization."""
    scanner = CameraScanner()
    
    assert not scanner.is_scanning
    assert scanner.found_cameras == []
    assert scanner.scan_thread is None


def test_camera_scanner_stop():
    """Test stopping a scan."""
    scanner = CameraScanner()
    scanner.is_scanning = True
    
    scanner.stop_scan()
    
    assert not scanner.is_scanning


def test_camera_scanner_get_found_cameras():
    """Test retrieving found cameras."""
    scanner = CameraScanner()
    
    camera = IPCamera(
        name="Test Camera",
        url="rtsp://192.168.1.100:554",
        protocol="rtsp",
        ip="192.168.1.100",
        port=554
    )
    scanner.found_cameras.append(camera)
    
    cameras = scanner.get_found_cameras()
    assert len(cameras) == 1
    assert cameras[0].name == "Test Camera"
    assert cameras is not scanner.found_cameras  # Should be a copy


@patch('src.services.ip_camera.test_rtsp_connection')
@patch('src.services.ip_camera.test_http_mjpeg')
def test_scan_ip_for_camera_rtsp_found(mock_http, mock_rtsp):
    """Test scanning IP when RTSP camera is found."""
    mock_rtsp.return_value = "rtsp://192.168.1.100:554/stream"
    mock_http.return_value = None
    
    camera = scan_ip_for_camera("192.168.1.100", "admin", "password")
    
    assert camera is not None
    assert camera.protocol == "rtsp"
    assert camera.ip == "192.168.1.100"
    assert camera.username == "admin"
    
    # RTSP should be tried first, so HTTP shouldn't be called
    mock_http.assert_not_called()


@patch('src.services.ip_camera.test_rtsp_connection')
@patch('src.services.ip_camera.test_http_mjpeg')
def test_scan_ip_for_camera_http_found(mock_http, mock_rtsp):
    """Test scanning IP when HTTP camera is found."""
    mock_rtsp.return_value = None
    mock_http.return_value = "http://192.168.1.100:80/video.mjpg"
    
    camera = scan_ip_for_camera("192.168.1.100")
    
    assert camera is not None
    assert camera.protocol == "mjpeg"
    assert camera.ip == "192.168.1.100"
    assert camera.port == 80  # First port in HTTP_PORTS list


@patch('src.services.ip_camera.test_rtsp_connection')
@patch('src.services.ip_camera.test_http_mjpeg')
def test_scan_ip_for_camera_not_found(mock_http, mock_rtsp):
    """Test scanning IP when no camera is found."""
    mock_rtsp.return_value = None
    mock_http.return_value = None
    
    camera = scan_ip_for_camera("192.168.1.100")
    
    assert camera is None


@patch('src.services.ip_camera.test_rtsp_connection')
def test_create_manual_camera_rtsp(mock_rtsp):
    """Test creating manual RTSP camera."""
    mock_rtsp.return_value = "rtsp://192.168.1.100:554/stream"
    
    camera = create_manual_camera("192.168.1.100", 554, "rtsp", "admin", "password")
    
    assert camera is not None
    assert camera.protocol == "rtsp"
    assert camera.username == "admin"


@patch('src.services.ip_camera.test_http_mjpeg')
def test_create_manual_camera_http(mock_http):
    """Test creating manual HTTP camera."""
    mock_http.return_value = "http://192.168.1.100:8080/video"
    
    camera = create_manual_camera("192.168.1.100", 8080, "http")
    
    assert camera is not None
    assert camera.protocol == "mjpeg"


@patch('src.services.ip_camera.test_rtsp_connection')
def test_create_manual_camera_fails(mock_rtsp):
    """Test creating manual camera when connection fails."""
    mock_rtsp.return_value = None
    
    camera = create_manual_camera("192.168.1.100", 554, "rtsp")
    
    assert camera is None
