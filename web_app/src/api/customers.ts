import api from './client';

export type CustomerStatus = 'active' | 'inactive';

export interface CustomerRecord {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  taxId?: string;
  status: CustomerStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CustomerSummary {
  orders: {
    count: number;
    totalAmount: number;
    balanceDue: number;
  };
  payments: {
    count: number;
    totalPaid: number;
  };
  outstandingBalance: number;
}

export interface CustomerListParams {
  page?: number;
  size?: number;
  search?: string | null;
  status?: CustomerStatus | 'all';
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    size: number;
    total: number;
    totalPages: number;
  };
}

export interface CustomerPayload {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  taxId?: string;
  status: CustomerStatus;
}

export const listCustomers = async (
  params: CustomerListParams
): Promise<PaginatedResponse<CustomerRecord>> => {
  const { data } = await api.get<PaginatedResponse<CustomerRecord>>('/customers', {
    params,
  });
  return data;
};

export const getCustomer = async (id: number): Promise<CustomerRecord> => {
  const { data } = await api.get<CustomerRecord>(`/customers/${id}`);
  return data;
};

export const createCustomer = async (payload: CustomerPayload): Promise<CustomerRecord> => {
  const { data } = await api.post<CustomerRecord>('/customers', payload);
  return data;
};

export const updateCustomer = async (
  id: number,
  payload: Partial<CustomerPayload>
): Promise<CustomerRecord> => {
  const { data } = await api.put<CustomerRecord>(`/customers/${id}`, payload);
  return data;
};

export const deactivateCustomer = async (id: number): Promise<CustomerRecord> => {
  const { data } = await api.post<CustomerRecord>(`/customers/${id}/deactivate`);
  return data;
};

export const fetchSummary = async (id: number): Promise<CustomerSummary> => {
  const { data } = await api.get<CustomerSummary>(`/customers/${id}/summary`);
  return data;
};

export const exportCustomersCsv = async (params: CustomerListParams = {}): Promise<Blob> => {
  const response = await api.get('/customers/export', {
    params,
    responseType: 'blob',
  });
  return response.data;
};

export const importCustomersCsv = async (
  file: File,
  mode: 'preview' | 'commit'
): Promise<{ rows: number; imported: number; errors: string[] }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', mode);

  const { data } = await api.post<{ rows: number; imported: number; errors: string[] }>(
    '/customers/import',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  );

  return data;
};
