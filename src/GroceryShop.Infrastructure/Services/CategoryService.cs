using GroceryShop.Core.DTOs;
using GroceryShop.Core.Interfaces;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Infrastructure.Services;

public class CategoryService : ICategoryService
{
    private readonly GroceryDbContext _db;

    public CategoryService(GroceryDbContext db) => _db = db;

    public async Task<IReadOnlyList<CategoryDto>> GetAllCategoriesAsync()
    {
        return await _db.Categories
            .Where(c => c.IsActive)
            .OrderBy(c => c.DisplayOrder)
            .Select(c => new CategoryDto(
                c.Id, c.Name, c.Slug, c.Description, c.ImageUrl, c.DisplayOrder, c.IsActive,
                c.Products.Count(p => p.IsAvailable)
            ))
            .ToListAsync();
    }

    public async Task<CategoryDto?> GetCategoryBySlugAsync(string slug)
    {
        return await _db.Categories
            .Where(c => c.Slug == slug && c.IsActive)
            .Select(c => new CategoryDto(
                c.Id, c.Name, c.Slug, c.Description, c.ImageUrl, c.DisplayOrder, c.IsActive,
                c.Products.Count(p => p.IsAvailable)
            ))
            .FirstOrDefaultAsync();
    }
}
