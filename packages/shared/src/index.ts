// Tipos de entidades
export enum EntityType {
  NATIONAL = 'NATIONAL',
  REGIONAL = 'REGIONAL',
  MUNICIPAL = 'MUNICIPAL',
  MINISTRY = 'MINISTRY',
  OTHER = 'OTHER',
}

export interface Entity {
  id: string;
  name: string;
  slug: string;
  description?: string;
  website?: string;
  logoUrl?: string;
  type: EntityType;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Tipos de procedimientos
export enum DifficultyLevel {
  EASY = 'EASY',
  MEDIUM = 'MEDIUM',
  HARD = 'HARD',
}

export interface Procedure {
  id: string;
  name: string;
  slug: string;
  description?: string;
  requirements: string[];
  steps: string[];
  cost?: number;
  duration?: string;
  officialUrl?: string;
  isOnline: boolean;
  difficulty: DifficultyLevel;
  category?: string;
  tags: string[];
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  entityId: string;
  entity?: Entity;
}

// Tipos de usuarios
export interface User {
  id: string;
  email: string;
  fullName?: string;
  phone?: string;
  documentType?: string;
  documentNumber?: string;
  isEmailVerified: boolean;
  isPremium: boolean;
  premiumExpiresAt?: Date;
  stripeCustomerId?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Tipos de consultas
export interface Query {
  id: string;
  message: string;
  response?: string;
  isAnswered: boolean;
  tokens?: number;
  responseTime?: number;
  satisfaction?: number;
  feedback?: string;
  sessionId?: string;
  createdAt: Date;
  userId?: string;
  user?: User;
  procedureId?: string;
  procedure?: Procedure;
}

// Tipos de documentos
export enum DocumentType {
  SOLICITUD = 'SOLICITUD',
  FORMATO = 'FORMATO',
  CHECKLIST = 'CHECKLIST',
  GUIDE = 'GUIDE',
}

export interface Document {
  id: string;
  title: string;
  type: DocumentType;
  content?: string;
  fileUrl?: string;
  fileName?: string;
  fileSize?: number;
  isDownloaded: boolean;
  downloadCount: number;
  createdAt: Date;
  userId: string;
  user?: User;
  queryId?: string;
  query?: Query;
  procedureId?: string;
  procedure?: Procedure;
}

// Tipos de pagos
export enum PaymentStatus {
  PENDING = 'PENDING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  REFUNDED = 'REFUNDED',
}

export interface Payment {
  id: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  stripePaymentId?: string;
  culqiChargeId?: string;
  description?: string;
  metadata?: Record<string, any>;
  createdAt: Date;
  userId: string;
  user?: User;
}

// Tipos de respuesta API
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    statusCode: number;
    stack?: string;
    name?: string;
  };
  message?: string;
  timestamp?: string;
  path?: string;
}

export interface PaginationResponse<T = any> {
  data: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    page?: number;
    pages?: number;
    hasMore?: boolean;
  };
}

// Constantes
export const DIFFICULTY_LABELS = {
  [DifficultyLevel.EASY]: 'Fácil',
  [DifficultyLevel.MEDIUM]: 'Intermedio',
  [DifficultyLevel.HARD]: 'Difícil',
};

export const ENTITY_TYPE_LABELS = {
  [EntityType.NATIONAL]: 'Nacional',
  [EntityType.REGIONAL]: 'Regional',
  [EntityType.MUNICIPAL]: 'Municipal',
  [EntityType.MINISTRY]: 'Ministerio',
  [EntityType.OTHER]: 'Otro',
};

export const DOCUMENT_TYPE_LABELS = {
  [DocumentType.SOLICITUD]: 'Solicitud',
  [DocumentType.FORMATO]: 'Formato',
  [DocumentType.CHECKLIST]: 'Lista de Verificación',
  [DocumentType.GUIDE]: 'Guía',
};

export const PAYMENT_STATUS_LABELS = {
  [PaymentStatus.PENDING]: 'Pendiente',
  [PaymentStatus.COMPLETED]: 'Completado',
  [PaymentStatus.FAILED]: 'Fallido',
  [PaymentStatus.REFUNDED]: 'Reembolsado',
};

// Utilidades
export function formatCurrency(amount: number, currency: string = 'PEN'): string {
  const symbols = {
    PEN: 'S/',
    USD: '$',
    EUR: '€',
  };
  
  const symbol = symbols[currency as keyof typeof symbols] || currency;
  return `${symbol} ${amount.toFixed(2)}`;
}

export function formatDuration(duration: string): string {
  const durations = {
    'minutes': 'minuto(s)',
    'hours': 'hora(s)',
    'days': 'día(s)',
    'weeks': 'semana(s)',
    'months': 'mes(es)',
    'years': 'año(s)',
  };
  
  let formatted = duration;
  Object.entries(durations).forEach(([en, es]) => {
    formatted = formatted.replace(new RegExp(en, 'gi'), es);
  });
  
  return formatted;
}

export function generateSlug(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remover acentos
    .replace(/[^a-z0-9\s-]/g, '') // Remover caracteres especiales
    .trim()
    .replace(/\s+/g, '-') // Reemplazar espacios con guiones
    .replace(/-+/g, '-'); // Remover guiones múltiples
}

export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function validateDNI(dni: string): boolean {
  return /^\d{8}$/.test(dni);
}

export function validateRUC(ruc: string): boolean {
  return /^\d{11}$/.test(ruc);
}

export function truncateText(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}
