import { apiClient } from '@/utils/apiClient';

export interface NotificationEmailsResponse {
  emails: string;
  email_list: string[];
  updated_at: string | null;
}

export async function fetchNotificationEmails(): Promise<NotificationEmailsResponse> {
  const res = await apiClient.get('/api/settings/notification-emails');
  if (!res.ok) throw new Error('Failed to fetch notification emails');
  return res.json();
}

export async function updateNotificationEmails(emails: string): Promise<NotificationEmailsResponse> {
  const res = await apiClient.put('/api/settings/notification-emails', { emails });
  if (!res.ok) throw new Error('Failed to update notification emails');
  return res.json();
}
