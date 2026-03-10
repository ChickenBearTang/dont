import axios, { AxiosError, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

// 1. 공통 인스턴스 생성
const axiosInstance = axios.create({
  // .env 파일의 환경변수 주입 (없을 경우를 대비한 최소한의 기본값 세팅)
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api', 
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 쿠키/세션 인증을 위해 추가
});

// 2. 요청(Request) 인터셉터
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 매 요청마다 로컬스토리지에서 토큰을 꺼내서 헤더에 주입
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 3. 응답(Response) 인터셉터
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // 401 에러(인증 실패/토큰 만료) 공통 처리
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 이미 재발급 중이라면 큐에 담고 대기
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return axiosInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // 토큰 재발급 API 호출 (쿠키 기반이므로 페이로드 불필요 가정)
        await axios.post(
          `${axiosInstance.defaults.baseURL}/auth/reissue`,
          {},
          { withCredentials: true }
        );
        
        isRefreshing = false;
        processQueue(null);
        
        // 실패했던 원래 요청 재시도
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        processQueue(refreshError);
        
        // [핵심] 재발급도 실패하면 전역 상태 로그아웃 처리
        console.error('세션이 만료되었습니다. 다시 로그인해주세요.');
        useAuthStore.getState().logout(); 
        
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
