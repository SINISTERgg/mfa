export const setStoredToken = (token) => {
  localStorage.setItem('access_token', token);
};

export const getStoredToken = () => {
  return localStorage.getItem('access_token');
};

export const setStoredUser = (user) => {
  localStorage.setItem('user', JSON.stringify(user));
};

export const getStoredUser = () => {
  try {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  } catch {
    return null;
  }
};

export const removeStoredToken = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const setStoredRefreshToken = (token) => {
  localStorage.setItem('refresh_token', token);
};

export const getStoredRefreshToken = () => {
  return localStorage.getItem('refresh_token');
};
