import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import deviceService from '../services/deviceService';
import { formatDate } from '../utils/helpers';
import './DeviceManagement.css';

const DeviceManagement = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await deviceService.getDevices();
      setDevices(response.devices);
    } catch (error) {
      toast.error('Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  const handleTrustDevice = async (deviceId) => {
    try {
      await deviceService.trustDevice(deviceId);
      toast.success('Device marked as trusted');
      fetchDevices();
    } catch (error) {
      toast.error(error);
    }
  };

  const handleRevokeDevice = async (deviceId) => {
    try {
      await deviceService.revokeDeviceTrust(deviceId);
      toast.success('Device trust revoked');
      fetchDevices();
    } catch (error) {
      toast.error(error);
    }
  };

  const handleDeleteDevice = async (deviceId) => {
    if (window.confirm('Are you sure you want to delete this device?')) {
      try {
        await deviceService.deleteDevice(deviceId);
        toast.success('Device deleted successfully');
        fetchDevices();
      } catch (error) {
        toast.error(error);
      }
    }
  };

  if (loading) {
    return <div className="loading">Loading devices...</div>;
  }

  return (
    <div className="device-management">
      <h3>Trusted Devices</h3>
      {devices.length === 0 ? (
        <p className="no-devices">No devices found</p>
      ) : (
        <div className="devices-list">
          {devices.map((device) => (
            <div key={device.id} className="device-card">
              <div className="device-info">
                <div className="device-icon">
                  {device.device_type === 'mobile' ? '📱' : '💻'}
                </div>
                <div className="device-details">
                  <h4>{device.device_name}</h4>
                  <p className="device-meta">
                    {device.browser} • {device.os}
                  </p>
                  <p className="device-date">
                    Last seen: {formatDate(device.last_seen)}
                  </p>
                </div>
              </div>
              <div className="device-status">
                {device.trust_valid ? (
                  <span className="badge badge-success">Trusted</span>
                ) : (
                  <span className="badge badge-danger">Not Trusted</span>
                )}
              </div>
              <div className="device-actions">
                {device.trust_valid ? (
                  <button
                    onClick={() => handleRevokeDevice(device.id)}
                    className="btn btn-secondary btn-sm"
                  >
                    Revoke Trust
                  </button>
                ) : (
                  <button
                    onClick={() => handleTrustDevice(device.id)}
                    className="btn btn-success btn-sm"
                  >
                    Trust Device
                  </button>
                )}
                <button
                  onClick={() => handleDeleteDevice(device.id)}
                  className="btn btn-danger btn-sm"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DeviceManagement;
