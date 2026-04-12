using GroceryShop.Core.DTOs;
using GroceryShop.Core.Models;

namespace GroceryShop.Core.Interfaces;

public interface IProductService
{
    Task<PagedResult<ProductDto>> GetProductsAsync(int page, int pageSize, Guid? categoryId = null, string? brand = null, bool? isOrganic = null, bool? dealsOnly = null, string? sortBy = null);
    Task<ProductDto?> GetProductByIdAsync(Guid id);
    Task<PagedResult<ProductDto>> GetProductsByCategorySlugAsync(string slug, int page, int pageSize);
    Task<PagedResult<ProductDto>> SearchProductsAsync(string query, int page, int pageSize);
    Task<ProductDto> CreateProductAsync(CreateProductDto dto);
    Task<ProductDto?> UpdateProductAsync(Guid id, CreateProductDto dto);
    Task<bool> DeleteProductAsync(Guid id);
}
