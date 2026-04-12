namespace GroceryShop.Core.DTOs;

public record CategoryDto(
    Guid Id,
    string Name,
    string Slug,
    string Description,
    string? ImageUrl,
    int DisplayOrder,
    bool IsActive,
    int ProductCount
);

public record CreateCategoryDto(
    string Name,
    string Slug,
    string Description,
    string? ImageUrl,
    int DisplayOrder
);
