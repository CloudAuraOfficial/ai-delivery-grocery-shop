using GroceryShop.Core.DTOs;
using GroceryShop.Core.Entities;
using GroceryShop.Core.Enums;
using GroceryShop.Core.Interfaces;
using GroceryShop.Core.Models;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Infrastructure.Services;

public class OrderService : IOrderService
{
    private readonly GroceryDbContext _db;
    private readonly ICartService _cartService;

    public OrderService(GroceryDbContext db, ICartService cartService)
    {
        _db = db;
        _cartService = cartService;
    }

    public async Task<PagedResult<OrderDto>> GetOrdersAsync(Guid userId, int page, int pageSize)
    {
        var query = _db.Orders
            .Include(o => o.Items).ThenInclude(i => i.Product)
            .Where(o => o.UserId == userId)
            .OrderByDescending(o => o.CreatedAt);

        var totalCount = await query.CountAsync();
        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(o => MapToDto(o))
            .ToListAsync();

        return new PagedResult<OrderDto> { Items = items, TotalCount = totalCount, Page = page, PageSize = pageSize };
    }

    public async Task<OrderDto?> GetOrderByIdAsync(Guid id)
    {
        return await _db.Orders
            .Include(o => o.Items).ThenInclude(i => i.Product)
            .Where(o => o.Id == id)
            .Select(o => MapToDto(o))
            .FirstOrDefaultAsync();
    }

    public async Task<OrderDto> CreateOrderAsync(Guid userId, string sessionId, CreateOrderDto dto)
    {
        var cart = await _cartService.GetCartAsync(sessionId);
        if (cart.Items.Count == 0)
            throw new InvalidOperationException("Cannot create order from empty cart");

        var orderNumber = $"ORD-{DateTime.UtcNow:yyyyMMdd}-{Guid.NewGuid().ToString()[..4].ToUpper()}";

        var order = new Order
        {
            UserId = userId,
            StoreId = dto.StoreId,
            OrderNumber = orderNumber,
            SubTotal = cart.SubTotal,
            Tax = cart.EstimatedTax,
            DeliveryFee = cart.DeliveryFee,
            Total = cart.Total,
            DeliveryAddress = dto.DeliveryAddress,
            Notes = dto.Notes,
            EstimatedDelivery = DateTime.UtcNow.AddMinutes(45),
            Items = cart.Items.Select(i => new OrderItem
            {
                ProductId = i.ProductId,
                Quantity = i.Quantity,
                UnitPrice = i.UnitPrice,
                LineTotal = i.LineTotal
            }).ToList()
        };

        _db.Orders.Add(order);
        await _db.SaveChangesAsync();
        await _cartService.ClearCartAsync(sessionId);

        return (await GetOrderByIdAsync(order.Id))!;
    }

    public async Task<OrderDto?> UpdateOrderStatusAsync(Guid id, OrderStatus status)
    {
        var order = await _db.Orders.FindAsync(id);
        if (order == null) return null;

        order.Status = status;
        await _db.SaveChangesAsync();
        return await GetOrderByIdAsync(id);
    }

    private static OrderDto MapToDto(Order o) => new(
        o.Id, o.OrderNumber, o.Status, o.SubTotal, o.Tax, o.DeliveryFee, o.Total,
        o.DeliveryAddress, o.EstimatedDelivery, o.CreatedAt,
        o.Items.Select(i => new OrderItemDto(
            i.ProductId, i.Product.Name, i.Quantity, i.UnitPrice, i.LineTotal
        )).ToList()
    );
}
