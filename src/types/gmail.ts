import { z } from 'zod';

// Gmail message schema
export const GmailMessageSchema = z.object({
  id: z.string(),
  threadId: z.string(),
  snippet: z.string(),
  historyId: z.string(),
  internalDate: z.string(),
  payload: z.object({
    partId: z.string().optional(),
    mimeType: z.string(),
    filename: z.string().optional(),
    headers: z.array(z.object({
      name: z.string(),
      value: z.string()
    })),
    body: z.object({
      attachmentId: z.string().optional(),
      size: z.number().optional(),
      data: z.string().optional()
    }).optional(),
    parts: z.array(z.any()).optional()
  }),
  sizeEstimate: z.number().optional(),
  raw: z.string().optional()
});

export type GmailMessage = z.infer<typeof GmailMessageSchema>;

// Gmail thread schema
export const GmailThreadSchema = z.object({
  id: z.string(),
  snippet: z.string(),
  historyId: z.string(),
  messages: z.array(GmailMessageSchema).optional()
});

export type GmailThread = z.infer<typeof GmailThreadSchema>;

// Gmail label schema
export const GmailLabelSchema = z.object({
  id: z.string(),
  name: z.string(),
  messageListVisibility: z.enum(['show', 'hide']).optional(),
  labelListVisibility: z.enum(['labelShow', 'labelShowIfUnread', 'labelHide']).optional(),
  type: z.enum(['system', 'user']).optional(),
  messagesTotal: z.number().optional(),
  messagesUnread: z.number().optional(),
  threadsTotal: z.number().optional(),
  threadsUnread: z.number().optional()
});

export type GmailLabel = z.infer<typeof GmailLabelSchema>;

// Configuration schemas
export const GmailConfigSchema = z.object({
  clientId: z.string(),
  clientSecret: z.string(),
  redirectUri: z.string(),
  credentialsPath: z.string().optional()
});

export type GmailConfig = z.infer<typeof GmailConfigSchema>;

// Tool input schemas
export const SendEmailInputSchema = z.object({
  to: z.string().or(z.array(z.string())),
  subject: z.string(),
  body: z.string(),
  cc: z.string().or(z.array(z.string())).optional(),
  bcc: z.string().or(z.array(z.string())).optional(),
  attachments: z.array(z.object({
    filename: z.string(),
    content: z.string(), // base64 encoded
    mimeType: z.string()
  })).optional()
});

export type SendEmailInput = z.infer<typeof SendEmailInputSchema>;

export const SearchEmailsInputSchema = z.object({
  query: z.string(),
  maxResults: z.number().min(1).max(500).default(10),
  labelIds: z.array(z.string()).optional(),
  includeSpamTrash: z.boolean().default(false)
});

export type SearchEmailsInput = z.infer<typeof SearchEmailsInputSchema>;

export const GetEmailInputSchema = z.object({
  messageId: z.string(),
  format: z.enum(['minimal', 'full', 'raw', 'metadata']).default('full')
});

export type GetEmailInput = z.infer<typeof GetEmailInputSchema>;

export const ModifyEmailInputSchema = z.object({
  messageId: z.string(),
  addLabelIds: z.array(z.string()).optional(),
  removeLabelIds: z.array(z.string()).optional()
});

export type ModifyEmailInput = z.infer<typeof ModifyEmailInputSchema>;

export const DeleteEmailInputSchema = z.object({
  messageId: z.string()
});

export type DeleteEmailInput = z.infer<typeof DeleteEmailInputSchema>;

export const CreateLabelInputSchema = z.object({
  name: z.string(),
  labelListVisibility: z.enum(['labelShow', 'labelShowIfUnread', 'labelHide']).default('labelShow'),
  messageListVisibility: z.enum(['show', 'hide']).default('show')
});

export type CreateLabelInput = z.infer<typeof CreateLabelInputSchema>;