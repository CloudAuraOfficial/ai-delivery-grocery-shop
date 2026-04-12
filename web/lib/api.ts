import type { Category, Product, Deal, Store, Cart, PagedResult, ChatResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const CHAT_BASE = process.env.NEXT_PUBLIC_CHAT_URL || "/api";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// Categories
export const getCategories = () => fetchJson<Category[]>(`${API_BASE}/categories`);
export const getCategoryBySlug = (slug: string) => fetchJson<Category>(`${API_BASE}/categories/${slug}`);

// Products
export const getProducts = (params?: Record<string, string>) => {
  const qs = new URLSearchParams(params).toString();
  return fetchJson<PagedResult<Product>>(`${API_BASE}/products${qs ? `?${qs}` : ""}`);
};
export const getProductById = (id: string) => fetchJson<Product>(`${API_BASE}/products/${id}`);
export const searchProducts = (q: string, page = 1) =>
  fetchJson<PagedResult<Product>>(`${API_BASE}/products/search?q=${encodeURIComponent(q)}&page=${page}`);
export const getProductsByCategory = (slug: string, page = 1) =>
  fetchJson<PagedResult<Product>>(`${API_BASE}/categories/${slug}/products?page=${page}`);

// Deals
export const getDeals = (type?: string) =>
  fetchJson<Deal[]>(`${API_BASE}/deals/${type || ""}`);
export const getBogoDeals = () => fetchJson<Deal[]>(`${API_BASE}/deals/bogo`);
export const getWeeklyDeals = () => fetchJson<Deal[]>(`${API_BASE}/deals/weekly`);
export const getDailyDeals = () => fetchJson<Deal[]>(`${API_BASE}/deals/daily`);

// Stores
export const getStores = () => fetchJson<Store[]>(`${API_BASE}/stores`);
export const getStoreById = (id: string) => fetchJson<Store>(`${API_BASE}/stores/${id}`);

// Cart
const getSessionId = () => {
  if (typeof window === "undefined") return "ssr";
  let id = localStorage.getItem("session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("session_id", id);
  }
  return id;
};

const cartHeaders = () => ({ "X-Session-Id": getSessionId() });

export const getCart = () => fetchJson<Cart>(`${API_BASE}/cart`, { headers: cartHeaders() });
export const addToCart = (productId: string, quantity = 1) =>
  fetchJson<Cart>(`${API_BASE}/cart/items`, {
    method: "POST",
    headers: cartHeaders(),
    body: JSON.stringify({ productId, quantity }),
  });
export const updateCartItem = (productId: string, quantity: number) =>
  fetchJson<Cart>(`${API_BASE}/cart/items/${productId}`, {
    method: "PUT",
    headers: cartHeaders(),
    body: JSON.stringify({ quantity }),
  });
export const removeCartItem = (productId: string) =>
  fetchJson<Cart>(`${API_BASE}/cart/items/${productId}`, {
    method: "DELETE",
    headers: cartHeaders(),
  });

// Chat
export const sendChatMessage = (message: string, sessionId?: string) =>
  fetchJson<ChatResponse>(`${CHAT_BASE}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  });
