// ==========================================
// User & Authentication
// ==========================================

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  phone?: string;
  role: "admin" | "accountant" | "business_owner" | "user";
  organization_id?: string;
  organization?: Organization;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  phone?: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

// ==========================================
// Organization
// ==========================================

export interface Organization {
  id: string;
  name: string;
  gstin?: string;
  pan?: string;
  address?: Address;
  phone?: string;
  email?: string;
  logo_url?: string;
  industry?: string;
  financial_year_start?: string;
  created_at: string;
  updated_at: string;
}

export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
}

// ==========================================
// Invoice
// ==========================================

export interface Invoice {
  id: string;
  invoice_number: string;
  organization_id: string;
  customer_name: string;
  customer_gstin?: string;
  customer_address?: Address;
  customer_email?: string;
  customer_phone?: string;
  items: InvoiceItem[];
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  currency: string;
  status: "draft" | "sent" | "paid" | "overdue" | "cancelled";
  issue_date: string;
  due_date: string;
  paid_date?: string;
  notes?: string;
  terms?: string;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: string;
  description: string;
  hsn_code?: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
  tax_type: "GST" | "IGST" | "CGST_SGST";
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  total_amount: number;
}

// ==========================================
// Tax Calculation
// ==========================================

export interface TaxResult {
  id: string;
  regime: "old" | "new";
  financial_year: string;
  gross_income: number;
  deductions: TaxDeduction[];
  total_deductions: number;
  taxable_income: number;
  tax_slabs: TaxSlab[];
  base_tax: number;
  surcharge: number;
  cess: number;
  total_tax: number;
  effective_rate: number;
  recommendation: string;
  created_at: string;
}

export interface TaxDeduction {
  section: string;
  description: string;
  amount: number;
  max_limit: number;
}

export interface TaxSlab {
  from: number;
  to: number | null;
  rate: number;
  tax: number;
}

// ==========================================
// Employee & Payroll
// ==========================================

export interface Employee {
  id: string;
  organization_id: string;
  employee_id: string;
  name: string;
  email: string;
  phone?: string;
  designation: string;
  department: string;
  date_of_joining: string;
  pan: string;
  bank_account?: BankAccount;
  salary_structure: SalaryStructure;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BankAccount {
  account_number: string;
  ifsc_code: string;
  bank_name: string;
  branch: string;
}

export interface SalaryStructure {
  basic: number;
  hra: number;
  da: number;
  special_allowance: number;
  other_allowances: number;
  gross_salary: number;
}

export interface Payslip {
  id: string;
  employee_id: string;
  employee: Employee;
  month: number;
  year: number;
  working_days: number;
  present_days: number;
  earnings: PayslipEarnings;
  deductions: PayslipDeductions;
  gross_pay: number;
  total_deductions: number;
  net_pay: number;
  status: "draft" | "processed" | "paid";
  payment_date?: string;
  created_at: string;
}

export interface PayslipEarnings {
  basic: number;
  hra: number;
  da: number;
  special_allowance: number;
  other_allowances: number;
  overtime: number;
  bonus: number;
}

export interface PayslipDeductions {
  pf: number;
  esi: number;
  professional_tax: number;
  tds: number;
  other_deductions: number;
}

// ==========================================
// AI Chat
// ==========================================

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: Record<string, unknown>;
  sources?: ChatSource[];
  timestamp: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  category: "tax" | "gst" | "compliance" | "general";
  messages: ChatMessage[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatSource {
  title: string;
  url?: string;
  section?: string;
  relevance_score: number;
}

// ==========================================
// API Response Wrappers
// ==========================================

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ApiError {
  success: false;
  message: string;
  errors?: Record<string, string[]>;
  status_code: number;
}
