import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchNotificationEmails,
  updateNotificationEmails,
} from '@/services/settingsService';

export function useNotificationEmails() {
  return useQuery({
    queryKey: ['notificationEmails'],
    queryFn: fetchNotificationEmails,
  });
}

export function useUpdateNotificationEmails() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (emails: string) => updateNotificationEmails(emails),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notificationEmails'] });
    },
  });
}
