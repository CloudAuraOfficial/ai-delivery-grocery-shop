using GroceryShop.Core.Enums;

namespace GroceryShop.Core.DTOs;

public record OrderDto(
    Guid Id,
    string OrderNumber,
    OrderStatus Status,
    decimal SubTotal,
    decimal Tax,
    decimal DeliveryFee,
    decimal Total,
    string DeliveryAddress,
    DateTime? EstimatedDelivery,
    DateTime CreatedAt,
    IReadOnlyList<OrderItemDto> Items
);

public record OrderItemDto(
    Guid ProductId,
    string ProductName,
    int Quantity,
    decimal UnitPrice,
    decimal LineTotal
);

public record CreateOrderDto(
    Guid StoreId,
    string DeliveryAddress,
    string? Notes
);
