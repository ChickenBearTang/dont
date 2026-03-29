const SESSION_REISSUE_ELIGIBLE_AUTH_CODES = new Set([
  'AUTH_401_1',
  'AUTH_401_3',
  'AUTH_401_4',
  'AUTH_401_5',
  'AUTH_401_6',
  'AUTH_401_7',
]);

const STATUS_SESSION_EXPIRED = new Set([401, 403]);

type ErrorWithResponse = {
  response?: {
    status?: number;
    data?: {
      code?: string;
      message?: string;
    };
  };
};

export const getErrorStatusCode = (error: unknown): number | undefined => {
  if (typeof error !== 'object' || error === null) {
    return undefined;
  }

  return (error as ErrorWithResponse).response?.status;
};

export const getErrorCode = (error: unknown): string | undefined => {
  if (typeof error !== 'object' || error === null) {
    return undefined;
  }

  return (error as ErrorWithResponse).response?.data?.code;
};

export const isSessionExpiredStatus = (status?: number): boolean => {
  if (status === undefined) {
    return false;
  }
  return STATUS_SESSION_EXPIRED.has(status);
};

export const isReissuable401Code = (code?: string): boolean => {
  if (!code) {
    return true;
  }

  if (code.startsWith('TOKEN_401_')) {
    return true;
  }

  return SESSION_REISSUE_ELIGIBLE_AUTH_CODES.has(code);
};
