import Link from "next/link";

const footerLinks = {
  Shop: [
    { href: "/products", label: "All Products" },
    { href: "/categories", label: "Categories" },
    { href: "/deals", label: "Deals" },
  ],
  Help: [
    { href: "/stores", label: "Store Locations" },
    { href: "/chat", label: "AI Assistant" },
    { href: "/about", label: "About" },
  ],
};

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-sm">
                AI
              </div>
              <div>
                <div className="font-bold text-white text-lg">AI Delivery Grocery Shop</div>
                <div className="text-xs text-gray-500">Lakeland, FL Area</div>
              </div>
            </div>
            <p className="text-sm text-gray-500 max-w-sm">
              AI-powered grocery delivery with 3,000+ products, smart deals, and a chatbot
              that knows your groceries. 9 store locations across Lakeland, Florida.
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h3 className="text-white font-semibold text-sm mb-3">{title}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-sm hover:text-white transition-colors">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-gray-800 mt-10 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-gray-600">
            Built with C#, Python, TypeScript, Azure, RAG &mdash; Portfolio project by CloudAura
          </p>
          <div className="flex gap-3 text-xs text-gray-600">
            <span>Next.js</span>
            <span>&middot;</span>
            <span>.NET 8</span>
            <span>&middot;</span>
            <span>FastAPI</span>
            <span>&middot;</span>
            <span>Qdrant</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
