using System.Text.Json;
using GroceryShop.Core.DTOs;
using GroceryShop.Core.Interfaces;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using StackExchange.Redis;

namespace GroceryShop.Infrastructure.Services;

public class CartService : ICartService
{
    private readonly IConnectionMultiplexer _redis;
    private readonly GroceryDbContext _db;
    private static readonly TimeSpan CartExpiry = TimeSpan.FromHours(24);

    public CartService(IConnectionMultiplexer redis, GroceryDbContext db)
    {
        _redis = redis;
        _db = db;
    }

    public async Task<CartDto> GetCartAsync(string sessionId)
    {
        var items = await GetCartItemsAsync(sessionId);
        return await BuildCartDtoAsync(items);
    }

    public async Task<CartDto> AddItemAsync(string sessionId, AddToCartDto dto)
    {
        var items = await GetCartItemsAsync(sessionId);
        var existing = items.Find(i => i.ProductId == dto.ProductId);

        if (existing != null)
            existing.Quantity += dto.Quantity;
        else
            items.Add(new CartItemInternal { ProductId = dto.ProductId, Quantity = dto.Quantity });

        await SaveCartAsync(sessionId, items);
        return await BuildCartDtoAsync(items);
    }

    public async Task<CartDto> UpdateItemAsync(string sessionId, Guid productId, UpdateCartItemDto dto)
    {
        var items = await GetCartItemsAsync(sessionId);
        var item = items.Find(i => i.ProductId == productId);

        if (item != null)
        {
            if (dto.Quantity <= 0)
                items.Remove(item);
            else
                item.Quantity = dto.Quantity;
        }

        await SaveCartAsync(sessionId, items);
        return await BuildCartDtoAsync(items);
    }

    public async Task<CartDto> RemoveItemAsync(string sessionId, Guid productId)
    {
        var items = await GetCartItemsAsync(sessionId);
        items.RemoveAll(i => i.ProductId == productId);
        await SaveCartAsync(sessionId, items);
        return await BuildCartDtoAsync(items);
    }

    public async Task ClearCartAsync(string sessionId)
    {
        var db = _redis.GetDatabase();
        await db.KeyDeleteAsync($"cart:{sessionId}");
    }

    private async Task<List<CartItemInternal>> GetCartItemsAsync(string sessionId)
    {
        var db = _redis.GetDatabase();
        var json = await db.StringGetAsync($"cart:{sessionId}");
        return json.HasValue ? JsonSerializer.Deserialize<List<CartItemInternal>>(json!)! : [];
    }

    private async Task SaveCartAsync(string sessionId, List<CartItemInternal> items)
    {
        var db = _redis.GetDatabase();
        var json = JsonSerializer.Serialize(items);
        await db.StringSetAsync($"cart:{sessionId}", json, CartExpiry);
    }

    private async Task<CartDto> BuildCartDtoAsync(List<CartItemInternal> items)
    {
        if (items.Count == 0)
            return new CartDto([], 0, 0, 0, 0, 0);

        var productIds = items.Select(i => i.ProductId).ToList();
        var products = await _db.Products
            .Include(p => p.Deals)
            .Where(p => productIds.Contains(p.Id))
            .ToListAsync();

        var cartItems = new List<CartItemDto>();
        foreach (var item in items)
        {
            var product = products.FirstOrDefault(p => p.Id == item.ProductId);
            if (product == null) continue;

            var activeDeal = product.Deals.FirstOrDefault(d => d.IsActive && d.EndDate > DateTime.UtcNow);
            var lineTotal = product.Price * item.Quantity;

            DealSummaryDto? dealSummary = activeDeal == null ? null : new DealSummaryDto(
                activeDeal.Id, activeDeal.DealType.ToString(), activeDeal.Title,
                activeDeal.DiscountPercent, activeDeal.DiscountAmount,
                activeDeal.BuyQuantity, activeDeal.GetQuantity, activeDeal.EndDate
            );

            cartItems.Add(new CartItemDto(
                product.Id, product.Name, product.Price, item.Quantity, lineTotal, dealSummary
            ));
        }

        var subTotal = cartItems.Sum(i => i.LineTotal);
        var tax = Math.Round(subTotal * 0.07m, 2); // FL sales tax
        var deliveryFee = subTotal >= 35 ? 0 : 5.99m;
        var total = subTotal + tax + deliveryFee;

        return new CartDto(cartItems, subTotal, tax, deliveryFee, total, cartItems.Sum(i => i.Quantity));
    }

    private class CartItemInternal
    {
        public Guid ProductId { get; set; }
        public int Quantity { get; set; }
    }
}
