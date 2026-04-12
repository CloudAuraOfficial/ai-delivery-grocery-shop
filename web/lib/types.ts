export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string;
  imageUrl: string | null;
  displayOrder: number;
  isActive: boolean;
  productCount: number;
}

export interface DealSummary {
  dealId: string;
  dealType: string;
  title: string;
  discountPercent: number | null;
  discountAmount: number | null;
  buyQuantity: number | null;
  getQuantity: number | null;
  endDate: string;
}

export interface Product {
  id: string;
  categoryId: string;
  categoryName: string;
  name: string;
  slug: string;
  description: string;
  brand: string | null;
  price: number;
  unit: string;
  weight: string | null;
  imageUrl: string | null;
  sku: string;
  isAvailable: boolean;
  isOrganic: boolean;
  isStoreBrand: boolean;
  tags: string | null;
  activeDeal: DealSummary | null;
}

export interface Deal {
  id: string;
  productId: string;
  productName: string;
  productPrice: number;
  productImageUrl: string | null;
  categoryName: string;
  dealType: "BOGO" | "WeeklyDeal" | "DailyDeal";
  title: string;
  description: string | null;
  discountPercent: number | null;
  discountAmount: number | null;
  buyQuantity: number | null;
  getQuantity: number | null;
  startDate: string;
  endDate: string;
  isActive: boolean;
}

export interface StoreHours {
  dayOfWeek: number;
  dayName: string;
  openTime: string;
  closeTime: string;
}

export interface Store {
  id: string;
  name: string;
  storeNumber: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  phone: string;
  latitude: number;
  longitude: number;
  isOpen: boolean;
  hours: StoreHours[];
}

export interface PagedResult<T> {
  items: T[];
  totalCount: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

export interface CartItem {
  productId: string;
  productName: string;
  unitPrice: number;
  quantity: number;
  lineTotal: number;
  appliedDeal: DealSummary | null;
}

export interface Cart {
  items: CartItem[];
  subTotal: number;
  estimatedTax: number;
  deliveryFee: number;
  total: number;
  itemCount: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface ProductReference {
  sku: string;
  name: string;
  price: number;
  category: string;
  dealType: string | null;
}

export interface ChatResponse {
  message: string;
  sessionId: string;
  products: ProductReference[];
  latencyMs: number | null;
  model: string | null;
}
