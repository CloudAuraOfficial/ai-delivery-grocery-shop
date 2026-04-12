"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCart, updateCartItem, removeCartItem } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import type { Cart } from "@/lib/types";

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCart().then(setCart).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleQuantity = async (productId: string, quantity: number) => {
    const updated = await updateCartItem(productId, quantity);
    setCart(updated);
  };

  const handleRemove = async (productId: string) => {
    const updated = await removeCartItem(productId);
    setCart(updated);
  };

  if (loading) {
    return <div className="max-w-4xl mx-auto px-4 py-16"><div className="animate-pulse bg-gray-100 rounded-xl h-64" /></div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-foreground mb-8">Shopping Cart</h1>

      {!cart || cart.items.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🛒</div>
          <h2 className="text-xl font-semibold text-foreground mb-2">Your cart is empty</h2>
          <p className="text-muted mb-6">Start shopping to add items to your cart.</p>
          <Link href="/products" className="px-6 py-3 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors">
            Browse Products
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Items */}
          <div className="lg:col-span-2 space-y-4">
            {cart.items.map((item) => (
              <div key={item.productId} className="flex gap-4 bg-white border border-border rounded-xl p-4">
                <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center text-2xl shrink-0">🛒</div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-foreground text-sm truncate">{item.productName}</h3>
                  <div className="text-sm text-muted">{formatPrice(item.unitPrice)} each</div>
                  {item.appliedDeal && (
                    <div className="text-xs text-red-600 font-medium mt-1">{item.appliedDeal.title}</div>
                  )}
                  <div className="flex items-center gap-3 mt-2">
                    <button
                      onClick={() => handleQuantity(item.productId, item.quantity - 1)}
                      className="w-8 h-8 rounded-lg border border-border text-sm hover:bg-surface"
                    >
                      -
                    </button>
                    <span className="text-sm font-medium w-8 text-center">{item.quantity}</span>
                    <button
                      onClick={() => handleQuantity(item.productId, item.quantity + 1)}
                      className="w-8 h-8 rounded-lg border border-border text-sm hover:bg-surface"
                    >
                      +
                    </button>
                    <button
                      onClick={() => handleRemove(item.productId)}
                      className="text-xs text-red-500 hover:text-red-700 ml-auto"
                    >
                      Remove
                    </button>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="font-bold text-foreground">{formatPrice(item.lineTotal)}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="bg-white border border-border rounded-xl p-6 h-fit sticky top-24">
            <h2 className="font-semibold text-foreground mb-4">Order Summary</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-muted">Subtotal ({cart.itemCount} items)</span><span>{formatPrice(cart.subTotal)}</span></div>
              <div className="flex justify-between"><span className="text-muted">Est. Tax (7% FL)</span><span>{formatPrice(cart.estimatedTax)}</span></div>
              <div className="flex justify-between">
                <span className="text-muted">Delivery</span>
                <span className={cart.deliveryFee === 0 ? "text-green-600 font-medium" : ""}>
                  {cart.deliveryFee === 0 ? "FREE" : formatPrice(cart.deliveryFee)}
                </span>
              </div>
              {cart.deliveryFee > 0 && (
                <div className="text-xs text-muted">Free delivery on orders over $35</div>
              )}
            </div>
            <div className="border-t border-border mt-4 pt-4 flex justify-between font-bold text-lg">
              <span>Total</span>
              <span>{formatPrice(cart.total)}</span>
            </div>
            <Link
              href="/checkout"
              className="block w-full mt-4 py-3 bg-primary text-white font-semibold rounded-lg text-center hover:bg-primary-dark transition-colors"
            >
              Proceed to Checkout
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
