import { useState, useEffect } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { useUnifiedAuth } from '../hooks/useUnifiedAuth';
import { useNotificationEmails, useUpdateNotificationEmails } from '../hooks/useSettings';
import { AuthGuard } from '../components/AuthGuard';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

export const Route = createFileRoute('/settings')({ component: SettingsPage });

function SettingsPage() {
  return (
    <AuthGuard>
      <SettingsContent />
    </AuthGuard>
  );
}

function SettingsContent() {
  const { user } = useUnifiedAuth();
  const [tabValue, setTabValue] = useState("profile");

  return (
    <div className="max-w-4xl mx-auto mt-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Account Settings</h1>

      <Card>
        <Tabs value={tabValue} onValueChange={setTabValue} className="w-full">
          <CardHeader>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="password">Password</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
              <TabsTrigger value="notifications">Notifications</TabsTrigger>
            </TabsList>
          </CardHeader>

          <CardContent>
            <TabsContent value="profile" className="space-y-4">
              <h2 className="text-xl font-semibold mb-4">Profile Information</h2>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input id="firstName" defaultValue={user?.first_name} disabled />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input id="lastName" defaultValue={user?.last_name} disabled />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" defaultValue={user?.email} disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Input id="role" defaultValue={user?.role} disabled />
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                Profile editing is currently disabled. Contact an administrator to update your information.
              </p>
            </TabsContent>

            <TabsContent value="password" className="space-y-4">
              <h2 className="text-xl font-semibold mb-4">Change Password</h2>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <Input id="currentPassword" type="password" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <Input id="newPassword" type="password" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input id="confirmPassword" type="password" />
                </div>
                <Button className="mt-4" disabled>
                  Update Password
                </Button>
                <p className="text-sm text-muted-foreground">
                  Password changes are currently disabled.
                </p>
              </div>
            </TabsContent>

            <TabsContent value="security" className="space-y-4">
              <h2 className="text-xl font-semibold mb-4">Security Settings</h2>
              <p className="text-muted-foreground">
                Two-factor authentication and other security settings will be available here.
              </p>
            </TabsContent>

            <TabsContent value="notifications" className="space-y-4">
              <NotificationsTab />
            </TabsContent>
          </CardContent>
        </Tabs>
      </Card>
    </div>
  );
}

function NotificationsTab() {
  const { data, isLoading } = useNotificationEmails();
  const updateMutation = useUpdateNotificationEmails();
  const [emailsInput, setEmailsInput] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (data) {
      setEmailsInput(data.emails);
    }
  }, [data]);

  const handleSave = () => {
    setSaved(false);
    updateMutation.mutate(emailsInput, {
      onSuccess: () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      },
    });
  };

  if (isLoading) {
    return <p className="text-muted-foreground">Loading notification settings...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Email Notifications</h2>
        <p className="text-sm text-muted-foreground">
          When an order is approved, the generated Office Order and Works Order
          spreadsheets will be emailed to the addresses below.
        </p>
      </div>

      {data?.email_list && data.email_list.length > 0 && (
        <div className="space-y-2">
          <Label>Current recipients</Label>
          <div className="flex flex-wrap gap-2">
            {data.email_list.map((email) => (
              <Badge key={email} variant="secondary">{email}</Badge>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="notificationEmails">Notification email addresses</Label>
        <Textarea
          id="notificationEmails"
          placeholder="e.g. sales@example.com, manager@example.com"
          value={emailsInput}
          onChange={(e) => setEmailsInput(e.target.value)}
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          Separate multiple addresses with commas. Leave blank to disable notifications.
        </p>
      </div>

      {updateMutation.isError && (
        <Alert variant="destructive">
          <AlertDescription>
            {updateMutation.error?.message || 'Failed to save notification settings.'}
          </AlertDescription>
        </Alert>
      )}

      {saved && (
        <Alert>
          <AlertDescription>Notification settings saved successfully.</AlertDescription>
        </Alert>
      )}

      <Button
        onClick={handleSave}
        disabled={updateMutation.isPending}
      >
        {updateMutation.isPending ? 'Saving...' : 'Save'}
      </Button>
    </div>
  );
}
