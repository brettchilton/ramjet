import { useQuery } from '@tanstack/react-query';
import { fetchEmail, getSourceAttachmentUrl } from '@/services/orderService';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Download, FileText, Image, Mail } from 'lucide-react';
import type { EmailAttachment } from '@/types/orders';

interface OrderSourcePanelProps {
  emailId?: number;
  orderId: string;
}

export function OrderSourcePanel({ emailId, orderId }: OrderSourcePanelProps) {
  if (!emailId) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p>No source email linked to this order</p>
      </div>
    );
  }

  return <EmailSourceContent emailId={emailId} orderId={orderId} />;
}

function EmailSourceContent({
  emailId,
  orderId,
}: {
  emailId: number;
  orderId: string;
}) {
  const { data: email, isLoading } = useQuery({
    queryKey: ['email', emailId],
    queryFn: () => fetchEmail(emailId),
  });

  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!email) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p>Email not found</p>
      </div>
    );
  }

  const pdfAttachments = email.attachments.filter(
    (a) => a.content_type === 'application/pdf'
  );
  const imageAttachments = email.attachments.filter((a) =>
    a.content_type?.startsWith('image/')
  );
  const otherAttachments = email.attachments.filter(
    (a) =>
      a.content_type !== 'application/pdf' &&
      !a.content_type?.startsWith('image/')
  );

  return (
    <Tabs defaultValue="email" className="h-full">
      <TabsList className="w-full justify-start">
        <TabsTrigger value="email" className="gap-1.5">
          <Mail className="h-3.5 w-3.5" />
          Email
        </TabsTrigger>
        {pdfAttachments.map((att) => (
          <TabsTrigger key={att.id} value={`pdf-${att.id}`} className="gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            {att.filename || 'PDF'}
          </TabsTrigger>
        ))}
        {imageAttachments.map((att) => (
          <TabsTrigger key={att.id} value={`img-${att.id}`} className="gap-1.5">
            <Image className="h-3.5 w-3.5" />
            {att.filename || 'Image'}
          </TabsTrigger>
        ))}
      </TabsList>

      <TabsContent value="email" className="mt-4 space-y-3">
        <div className="space-y-1 text-sm">
          <p>
            <span className="font-medium text-muted-foreground">From:</span>{' '}
            {email.sender || '—'}
          </p>
          <p>
            <span className="font-medium text-muted-foreground">Subject:</span>{' '}
            {email.subject || '—'}
          </p>
          <p>
            <span className="font-medium text-muted-foreground">Received:</span>{' '}
            {email.received_at
              ? new Date(email.received_at).toLocaleString('en-AU')
              : '—'}
          </p>
        </div>
        <div className="rounded-md border p-4 bg-muted/30 text-sm whitespace-pre-wrap max-h-[500px] overflow-y-auto">
          {email.body_text || '(No text body)'}
        </div>
        {otherAttachments.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">
              Other Attachments
            </p>
            {otherAttachments.map((att) => (
              <AttachmentDownloadLink
                key={att.id}
                attachment={att}
                orderId={orderId}
              />
            ))}
          </div>
        )}
      </TabsContent>

      {pdfAttachments.map((att) => (
        <TabsContent key={att.id} value={`pdf-${att.id}`} className="mt-4">
          <PdfViewer orderId={orderId} attachment={att} />
        </TabsContent>
      ))}

      {imageAttachments.map((att) => (
        <TabsContent key={att.id} value={`img-${att.id}`} className="mt-4">
          <div className="space-y-2">
            <img
              src={getSourceAttachmentUrl(orderId, att.id)}
              alt={att.filename || 'Attachment'}
              className="max-w-full rounded-md border"
            />
            <AttachmentDownloadLink attachment={att} orderId={orderId} />
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}

function PdfViewer({
  orderId,
  attachment,
}: {
  orderId: string;
  attachment: EmailAttachment;
}) {
  const url = getSourceAttachmentUrl(orderId, attachment.id);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{attachment.filename}</p>
        <AttachmentDownloadLink attachment={attachment} orderId={orderId} />
      </div>
      <iframe
        src={url}
        title={attachment.filename || 'PDF'}
        className="w-full h-[600px] rounded-md border bg-white"
      />
    </div>
  );
}

function AttachmentDownloadLink({
  attachment,
  orderId,
}: {
  attachment: EmailAttachment;
  orderId: string;
}) {
  const url = getSourceAttachmentUrl(orderId, attachment.id);
  return (
    <Button variant="outline" size="sm" asChild>
      <a href={url} download={attachment.filename || 'attachment'} target="_blank" rel="noopener noreferrer">
        <Download className="mr-1.5 h-3.5 w-3.5" />
        {attachment.filename || 'Download'}
      </a>
    </Button>
  );
}
