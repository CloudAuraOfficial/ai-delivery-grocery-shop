namespace GroceryShop.Core.DTOs;

public record CartDto(
    IReadOnlyList<CartItemDto> Items,
    decimal SubTotal,
    decimal EstimatedTax,
    decimal DeliveryFee,
    decimal Total,
    int ItemCount
);

public record CartItemDto(
    Guid ProductId,
    string ProductName,
    decimal UnitPrice,
    int Quantity,
    decimal LineTotal,
    DealSummaryDto? AppliedDeal
);

public record AddToCartDto(
    Guid ProductId,
    int Quantity = 1
);

public record UpdateCartItemDto(
    int Quantity
);
