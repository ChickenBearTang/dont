import React, { useState, useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { createRouter } from '@/app/router';
import '@/styles/index.css';

// TODO: UserData 타입은 추후 외부(shared/types 또는 features/user/types)에 제대로 된 인터페이스로 정의해야 합니다.
interface UserData {
  nickname: string;
  isKdt: boolean;
  housingExpense: number;
  monthlyFixedCost: number;
  goalAmount: number;
  connected: boolean;
}

export function App() {
  const [userData, setUserData] = useState<UserData>({
    nickname: '',
    isKdt: false,
    housingExpense: 0,
    monthlyFixedCost: 0,
    goalAmount: 0,
    connected: false,
  });
  
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const savedAuth = localStorage.getItem('dont_auth');
    const savedUser = localStorage.getItem('dont_user_data');
    if (savedAuth === 'true') {
      setIsAuthenticated(true);
    }
    if (savedUser) {
      setUserData(JSON.parse(savedUser));
    }
  }, []);

  const updateUserData = (data: Partial<UserData>) => {
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

  // 현재 상태를 주입하여 라우터 인스턴스 생성
  const router = createRouter(isAuthenticated, userData, handleLogout);

  return (
    <React.StrictMode>
      {/* React Query, 테마(Theme) 등 전역 Provider를 추가한다면 RouterProvider 바깥을 감싸주세요 */}
      <RouterProvider router={router} />
    </React.StrictMode>
  );
}
