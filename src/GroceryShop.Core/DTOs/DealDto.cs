using GroceryShop.Core.Enums;

namespace GroceryShop.Core.DTOs;

public record DealDto(
    Guid Id,
    Guid ProductId,
    string ProductName,
    decimal ProductPrice,
    string? ProductImageUrl,
    string CategoryName,
    DealType DealType,
    string Title,
    string? Description,
    decimal? DiscountPercent,
    decimal? DiscountAmount,
    int? BuyQuantity,
    int? GetQuantity,
    DateTime StartDate,
    DateTime EndDate,
    bool IsActive
);

public record CreateDealDto(
    Guid ProductId,
    DealType DealType,
    string Title,
    string? Description,
    decimal? DiscountPercent,
    decimal? DiscountAmount,
    int? BuyQuantity,
    int? GetQuantity,
    DateTime StartDate,
    DateTime EndDate
);
