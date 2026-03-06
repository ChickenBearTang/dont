import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Landing, Login, Signup } from './domains/auth';
import {
  Onboarding,
  FinanceConnect,
  LoadingScreen,
  SaveboxSetup,
  SuccessScreen,
} from './domains/onboarding';
import { Dashboard } from './domains/dashboard';
import PublicLayout from './components/common/PublicLayout';
import AppLayout from './components/common/AppLayout';
import './styles/index.css';

function App() {
  const [userData, setUserData] = useState({
    nickname: '',
    isKdt: false,
    housingExpense: 0,
    monthlyFixedCost: 0,
    goalAmount: 0,
    connected: false,
  });
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    const savedAuth = localStorage.getItem('dont_auth');
    const savedUser = localStorage.getItem('dont_user_data');
    if (savedAuth === 'true') {
      setIsAuthenticated(true);
    }
    if (savedUser) {
      setUserData(JSON.parse(savedUser));
    }
  }, []);

  const updateUserData = (data) => {
    setUserData((prev) => {
      const newData = { ...prev, ...data };
      localStorage.setItem('dont_user_data', JSON.stringify(newData));
      return newData;
    });
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    localStorage.setItem('dont_auth', 'true');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('dont_auth');
    localStorage.removeItem('dont_user_data');
  };

  return (
    <Routes>
      {/* Public Routes (No Header) */}
      <Route element={<PublicLayout />}>
        <Route
          path="/"
          element={
            isAuthenticated ? <Navigate to="/dashboard" /> : <Landing onSocialLogin={handleLogin} />
          }
        />
        <Route path="/login" element={<Login onSocialLogin={handleLogin} />} />
        <Route path="/onboarding" element={<Onboarding updateUser={updateUserData} />} />
        <Route path="/signup" element={<Signup onNext={() => navigate('/finance-connect')} />} />
        <Route path="/finance-connect" element={<FinanceConnect updateUser={updateUserData} />} />
        <Route path="/loading" element={<LoadingScreen />} />
        <Route
          path="/savebox-setup"
          element={<SaveboxSetup userData={userData} onComplete={updateUserData} />}
        />
        <Route
          path="/success"
          element={
            <SuccessScreen
              onComplete={() => {
                handleLogin();
                navigate('/dashboard');
              }}
            />
          }
        />
      </Route>

      {/* App Routes (With Header) */}
      <Route
        element={
          <AppLayout
            userData={userData}
            onLogout={handleLogout}
            isAuthenticated={isAuthenticated}
          />
        }
      >
        <Route
          path="/dashboard"
          element={
            isAuthenticated ? (
              <Dashboard userData={userData} onLogout={handleLogout} />
            ) : (
              <Navigate to="/" />
            )
          }
        />
      </Route>
    </Routes>
  );
}

export default App;
