import sys
import os
from unittest.mock import patch, mock_open
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rgb_control.backend import Backend

@patch("subprocess.run")
def test_is_service_active(mock_run):
    backend = Backend()
    
    mock_run.return_value.stdout = "active\n"
    assert backend.is_service_active() is True
    
    mock_run.return_value.stdout = "inactive\n"
    assert backend.is_service_active() is False

@patch("subprocess.run")
def test_set_service_state(mock_run):
    backend = Backend()
    mock_run.return_value.returncode = 0
    assert backend.set_service_state(True) is True
    mock_run.assert_called_with(["pkexec", "systemctl", "start", "openrbg.service"], capture_output=True)
    
    assert backend.set_service_state(False) is True
    mock_run.assert_called_with(["pkexec", "systemctl", "stop", "openrbg.service"], capture_output=True)

@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="on")
def test_is_led_mode_active(mock_file, mock_exists):
    backend = Backend()
    assert backend.is_led_mode_active() is True
    
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="off")
def test_is_led_mode_active_off(mock_file, mock_exists):
    backend = Backend()
    assert backend.is_led_mode_active() is False

@patch("os.path.exists", side_effect=lambda x: False) # Force it to not find the script to trigger openrgb fallback
@patch("subprocess.Popen")
def test_apply_color_fallback(mock_popen, mock_exists):
    backend = Backend()
    backend.apply_color("#FF5500", "Laranja")
    mock_popen.assert_called_with(["openrgb", "--device", "0", "--mode", "static", "--color", "FF5500"])
