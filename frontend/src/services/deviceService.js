import api from './api';

const deviceService = {
  // Get all devices
  getDevices: async () => {
    const response = await api.get('/api/device/list');
    return response.data;
  },

  // Trust device
  trustDevice: async (deviceId) => {
    const response = await api.post(`/api/device/${deviceId}/trust`);
    return response.data;
  },

  // Revoke device trust
  revokeDeviceTrust: async (deviceId) => {
    const response = await api.post(`/api/device/${deviceId}/revoke`);
    return response.data;
  },

  // Delete device
  deleteDevice: async (deviceId) => {
    const response = await api.delete(`/api/device/${deviceId}`);
    return response.data;
  },
};

export default deviceService;
