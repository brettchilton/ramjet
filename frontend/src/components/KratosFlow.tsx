import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface KratosFlowProps {
  flow: any;
  onSubmit: (data: any) => Promise<{ success: boolean; error?: any }>;
  loading?: boolean;
}

export function KratosFlow({ flow, onSubmit, loading = false }: KratosFlowProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!flow || !flow.ui) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    console.log('Submitting form data:', formData);
    console.log('Flow:', flow);

    try {
      const result = await onSubmit(formData);
      
      if (!result.success && result.error) {
        // Handle Kratos error response
        if (result.error.ui?.messages?.[0]) {
          setError(result.error.ui.messages[0].text);
        } else if (result.error.error?.message) {
          setError(result.error.error.message);
        } else {
          setError('An error occurred. Please try again.');
        }
      }
    } catch (err) {
      setError('An unexpected error occurred.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleInputChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Seed required hidden fields and defaults when the flow changes
  useEffect(() => {
    if (!flow?.ui?.nodes) return;
    const initial: Record<string, any> = {};

    for (const node of flow.ui.nodes) {
      const { type, attributes } = node;
      if (type === 'input' && attributes?.type === 'hidden' && attributes?.name) {
        initial[attributes.name] = attributes.value;
      }
      if (attributes?.name === 'csrf_token') {
        initial['csrf_token'] = attributes.value;
      }
      if (attributes?.name === 'traits.role' && flow.request_url?.includes('/registration')) {
        if (!formData['traits.role']) {
          initial['traits.role'] = 'warehouse';
        }
      }
    }

    if (Object.keys(initial).length > 0) {
      setFormData(prev => ({ ...initial, ...prev }));
    }
  }, [flow]);

  const renderNode = (node: any) => {
    const { type, attributes, messages, meta } = node;

    // Skip certain nodes from rendering (but keep values via effect)
    if (type === 'input' && attributes.type === 'hidden') {
      return null;
    }
    if (attributes.name === 'csrf_token') {
      return null;
    }
    if (attributes.name === 'traits.role' && flow.request_url?.includes('/registration')) {
      return null;
    }

    // Error messages for the field
    const fieldErrors = messages?.filter((m: any) => m.type === 'error') || [];
    const hasError = fieldErrors.length > 0;

    switch (type) {
      case 'input':
        switch (attributes.type) {
          case 'submit':
            return (
              <Button
                key={attributes.name}
                type="submit"
                className="w-full"
                disabled={submitting || loading}
                onClick={() => {
                  // Ensure the chosen strategy (e.g., password) is sent
                  if (attributes.name && attributes.value) {
                    handleInputChange(attributes.name, attributes.value);
                  }
                }}
              >
                {submitting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                ) : (
                  attributes.value
                )}
              </Button>
            );

          case 'email':
          case 'password':
          case 'text':
          case 'tel':
            return (
              <div key={attributes.name} className="space-y-2">
                <Label htmlFor={attributes.name}>
                  {attributes.name === 'identifier' 
                    ? 'Email' 
                    : (meta?.label?.text || attributes.name)}
                  {attributes.required && <span className="text-destructive ml-1">*</span>}
                </Label>
                <Input
                  id={attributes.name}
                  name={attributes.name}
                  type={attributes.name === 'identifier' ? 'email' : attributes.type}
                  required={attributes.required}
                  disabled={attributes.disabled}
                  value={formData[attributes.name] || attributes.value || ''}
                  onChange={(e) => handleInputChange(attributes.name, e.target.value)}
                  autoComplete={attributes.autocomplete || (attributes.name === 'identifier' ? 'email' : undefined)}
                  className={hasError ? 'border-destructive' : ''}
                />
                {hasError && (
                  <p className="text-sm text-destructive">{fieldErrors[0]?.text}</p>
                )}
              </div>
            );

          case 'checkbox':
            return (
              <div key={attributes.name} className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id={attributes.name}
                    name={attributes.name}
                    checked={formData[attributes.name] || false}
                    onCheckedChange={(checked) => handleInputChange(attributes.name, checked)}
                    disabled={attributes.disabled}
                  />
                  <Label 
                    htmlFor={attributes.name}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {meta?.label?.text || attributes.name}
                  </Label>
                </div>
                {hasError && (
                  <p className="text-sm text-destructive">{fieldErrors[0]?.text}</p>
                )}
              </div>
            );

          default:
            return null;
        }

      case 'script':
        // Handle WebAuthn or other scripts if needed
        return null;

      case 'text':
        return (
          <p key={meta?.label?.id} className="text-sm text-muted-foreground">
            {meta?.label?.text}
          </p>
        );

      default:
        return null;
    }
  };

  // Group nodes by their group
  const groupedNodes = flow.ui.nodes.reduce((acc: any, node: any) => {
    const group = node.group || 'default';
    if (!acc[group]) acc[group] = [];
    acc[group].push(node);
    return acc;
  }, {});
  
  console.log('Flow nodes:', flow.ui.nodes);
  console.log('Current formData:', formData);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Global flow messages */}
      {flow.ui.messages?.map((message: any, index: number) => (
        <Alert key={index} variant={message.type === 'error' ? 'destructive' : 'default'}>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      ))}

      {/* Error from submission */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Render nodes by group */}
      {Object.entries(groupedNodes).map(([group, nodes]: [string, any]) => (
        <div key={group} className="space-y-4">
          {group !== 'default' && group !== 'password' && group !== 'profile' && (
            <h3 className="text-lg font-semibold">
              {group.charAt(0).toUpperCase() + group.slice(1)}
            </h3>
          )}
          {nodes.map((node: any) => renderNode(node))}
        </div>
      ))}
    </form>
  );
}