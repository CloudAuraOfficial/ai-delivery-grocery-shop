namespace GroceryShop.Core.DTOs;

public record ProductDto(
    Guid Id,
    Guid CategoryId,
    string CategoryName,
    string Name,
    string Slug,
    string Description,
    string? Brand,
    decimal Price,
    string Unit,
    string? Weight,
    string? ImageUrl,
    string Sku,
    bool IsAvailable,
    bool IsOrganic,
    bool IsStoreBrand,
    string? Tags,
    DealSummaryDto? ActiveDeal
);

public record CreateProductDto(
    Guid CategoryId,
    string Name,
    string Description,
    string? Brand,
    decimal Price,
    string Unit,
    string? Weight,
    string? ImageUrl,
    bool IsOrganic,
    bool IsStoreBrand,
    string? NutritionInfo,
    string? Tags
);

public record DealSummaryDto(
    Guid DealId,
    string DealType,
    string Title,
    decimal? DiscountPercent,
    decimal? DiscountAmount,
    int? BuyQuantity,
    int? GetQuantity,
    DateTime EndDate
);
