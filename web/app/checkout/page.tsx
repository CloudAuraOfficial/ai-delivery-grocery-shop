"use client";

import { useState } from "react";
import Link from "next/link";

export default function CheckoutPage() {
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="text-6xl mb-4">🎉</div>
        <h1 className="text-2xl font-bold text-foreground mb-4">Order Placed!</h1>
        <p className="text-muted mb-8">
          Your order has been confirmed. Estimated delivery in 45 minutes.
          This is a demo — no real payment was processed.
        </p>
        <Link href="/products" className="px-6 py-3 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors">
          Continue Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-foreground mb-8">Checkout</h1>

      <div className="space-y-6">
        <div className="bg-white border border-border rounded-xl p-6">
          <h2 className="font-semibold text-foreground mb-4">Delivery Address</h2>
          <div className="space-y-4">
            <input type="text" placeholder="Full Name" className="w-full px-4 py-2.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
            <input type="text" placeholder="Street Address" className="w-full px-4 py-2.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
            <div className="grid grid-cols-2 gap-4">
              <input type="text" placeholder="City" defaultValue="Lakeland" className="px-4 py-2.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
              <input type="text" placeholder="ZIP Code" className="px-4 py-2.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
            </div>
          </div>
        </div>

        <div className="bg-white border border-border rounded-xl p-6">
          <h2 className="font-semibold text-foreground mb-4">Delivery Notes</h2>
          <textarea placeholder="Leave at door, ring doorbell, etc." rows={3} className="w-full px-4 py-2.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none" />
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          This is a <strong>demo checkout</strong>. No real payment will be processed.
        </div>

        <button
          onClick={() => setSubmitted(true)}
          className="w-full py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-dark transition-colors"
        >
          Place Order (Demo)
        </button>
      </div>
    </div>
  );
}
