


export const accountKeys = {
  all: ['account'] as const,
  lists: () => [...accountKeys.all, 'list'] as const,
  list: (filters: object) => [...accountKeys.lists(), { filters }] as const,
  details: () => [...accountKeys.all, 'detail'] as const,
  detail: (id: number) => [...accountKeys.details(), id] as const,
  transactions: (id: number, filters: object) =>
    [...accountKeys.detail(id), 'transactions', { filters }] as const,
  savings: () => [...accountKeys.all, 'savings'] as const,
};
