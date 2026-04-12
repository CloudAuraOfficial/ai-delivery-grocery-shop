using GroceryShop.Core.DTOs;
using GroceryShop.Core.Enums;
using GroceryShop.Core.Models;

namespace GroceryShop.Core.Interfaces;

public interface IOrderService
{
    Task<PagedResult<OrderDto>> GetOrdersAsync(Guid userId, int page, int pageSize);
    Task<OrderDto?> GetOrderByIdAsync(Guid id);
    Task<OrderDto> CreateOrderAsync(Guid userId, string sessionId, CreateOrderDto dto);
    Task<OrderDto?> UpdateOrderStatusAsync(Guid id, OrderStatus status);
}
