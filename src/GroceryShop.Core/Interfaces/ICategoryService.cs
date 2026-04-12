using GroceryShop.Core.DTOs;

namespace GroceryShop.Core.Interfaces;

public interface ICategoryService
{
    Task<IReadOnlyList<CategoryDto>> GetAllCategoriesAsync();
    Task<CategoryDto?> GetCategoryBySlugAsync(string slug);
}
