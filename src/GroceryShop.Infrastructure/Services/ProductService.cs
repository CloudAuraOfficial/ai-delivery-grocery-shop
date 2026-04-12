using GroceryShop.Core.DTOs;
using GroceryShop.Core.Entities;
using GroceryShop.Core.Interfaces;
using GroceryShop.Core.Models;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Infrastructure.Services;

public class ProductService : IProductService
{
    private readonly GroceryDbContext _db;

    public ProductService(GroceryDbContext db) => _db = db;

    public async Task<PagedResult<ProductDto>> GetProductsAsync(
        int page, int pageSize, Guid? categoryId = null, string? brand = null,
        bool? isOrganic = null, bool? dealsOnly = null, string? sortBy = null)
    {
        var query = _db.Products
            .Include(p => p.Category)
            .Include(p => p.Deals)
            .Where(p => p.IsAvailable)
            .AsQueryable();

        if (categoryId.HasValue)
            query = query.Where(p => p.CategoryId == categoryId.Value);
        if (!string.IsNullOrEmpty(brand))
            query = query.Where(p => p.Brand != null && p.Brand.ToLower().Contains(brand.ToLower()));
        if (isOrganic == true)
            query = query.Where(p => p.IsOrganic);
        if (dealsOnly == true)
            query = query.Where(p => p.Deals.Any(d => d.IsActive && d.EndDate > DateTime.UtcNow));

        query = sortBy?.ToLower() switch
        {
            "price_asc" => query.OrderBy(p => p.Price),
            "price_desc" => query.OrderByDescending(p => p.Price),
            "name" => query.OrderBy(p => p.Name),
            _ => query.OrderBy(p => p.Name)
        };

        var totalCount = await query.CountAsync();
        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(p => MapToDto(p))
            .ToListAsync();

        return new PagedResult<ProductDto>
        {
            Items = items,
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize
        };
    }

    public async Task<ProductDto?> GetProductByIdAsync(Guid id)
    {
        return await _db.Products
            .Include(p => p.Category)
            .Include(p => p.Deals)
            .Where(p => p.Id == id)
            .Select(p => MapToDto(p))
            .FirstOrDefaultAsync();
    }

    public async Task<PagedResult<ProductDto>> GetProductsByCategorySlugAsync(string slug, int page, int pageSize)
    {
        var category = await _db.Categories.FirstOrDefaultAsync(c => c.Slug == slug);
        if (category == null)
            return new PagedResult<ProductDto> { Items = [], TotalCount = 0, Page = page, PageSize = pageSize };

        return await GetProductsAsync(page, pageSize, categoryId: category.Id);
    }

    public async Task<PagedResult<ProductDto>> SearchProductsAsync(string query, int page, int pageSize)
    {
        var q = query.ToLower();
        var dbQuery = _db.Products
            .Include(p => p.Category)
            .Include(p => p.Deals)
            .Where(p => p.IsAvailable && (
                p.Name.ToLower().Contains(q) ||
                p.Description.ToLower().Contains(q) ||
                (p.Brand != null && p.Brand.ToLower().Contains(q)) ||
                (p.Tags != null && p.Tags.ToLower().Contains(q))
            ))
            .OrderBy(p => p.Name);

        var totalCount = await dbQuery.CountAsync();
        var items = await dbQuery
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(p => MapToDto(p))
            .ToListAsync();

        return new PagedResult<ProductDto>
        {
            Items = items,
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize
        };
    }

    public async Task<ProductDto> CreateProductAsync(CreateProductDto dto)
    {
        var product = new Product
        {
            CategoryId = dto.CategoryId,
            Name = dto.Name,
            Slug = GenerateSlug(dto.Name),
            Description = dto.Description,
            Brand = dto.Brand,
            Price = dto.Price,
            Unit = dto.Unit,
            Weight = dto.Weight,
            ImageUrl = dto.ImageUrl,
            Sku = await GenerateSkuAsync(dto.CategoryId),
            IsOrganic = dto.IsOrganic,
            IsStoreBrand = dto.IsStoreBrand,
            NutritionInfo = dto.NutritionInfo,
            Tags = dto.Tags
        };

        _db.Products.Add(product);
        await _db.SaveChangesAsync();

        return (await GetProductByIdAsync(product.Id))!;
    }

    public async Task<ProductDto?> UpdateProductAsync(Guid id, CreateProductDto dto)
    {
        var product = await _db.Products.FindAsync(id);
        if (product == null) return null;

        product.CategoryId = dto.CategoryId;
        product.Name = dto.Name;
        product.Slug = GenerateSlug(dto.Name);
        product.Description = dto.Description;
        product.Brand = dto.Brand;
        product.Price = dto.Price;
        product.Unit = dto.Unit;
        product.Weight = dto.Weight;
        product.ImageUrl = dto.ImageUrl;
        product.IsOrganic = dto.IsOrganic;
        product.IsStoreBrand = dto.IsStoreBrand;
        product.NutritionInfo = dto.NutritionInfo;
        product.Tags = dto.Tags;

        await _db.SaveChangesAsync();
        return await GetProductByIdAsync(id);
    }

    public async Task<bool> DeleteProductAsync(Guid id)
    {
        var product = await _db.Products.FindAsync(id);
        if (product == null) return false;

        product.IsAvailable = false;
        await _db.SaveChangesAsync();
        return true;
    }

    private static ProductDto MapToDto(Product p)
    {
        var activeDeal = p.Deals.FirstOrDefault(d => d.IsActive && d.EndDate > DateTime.UtcNow);
        return new ProductDto(
            p.Id, p.CategoryId, p.Category.Name, p.Name, p.Slug,
            p.Description, p.Brand, p.Price, p.Unit, p.Weight,
            p.ImageUrl, p.Sku, p.IsAvailable, p.IsOrganic, p.IsStoreBrand, p.Tags,
            activeDeal == null ? null : new DealSummaryDto(
                activeDeal.Id, activeDeal.DealType.ToString(), activeDeal.Title,
                activeDeal.DiscountPercent, activeDeal.DiscountAmount,
                activeDeal.BuyQuantity, activeDeal.GetQuantity, activeDeal.EndDate
            )
        );
    }

    private static string GenerateSlug(string name)
    {
        return name.ToLower()
            .Replace("&", "and")
            .Replace("'", "")
            .Replace(" ", "-")
            .Replace("--", "-")
            .Trim('-');
    }

    private async Task<string> GenerateSkuAsync(Guid categoryId)
    {
        var category = await _db.Categories.FindAsync(categoryId);
        var prefix = category?.Slug?.ToUpper()[..Math.Min(3, category.Slug.Length)] ?? "GEN";
        var count = await _db.Products.CountAsync(p => p.CategoryId == categoryId);
        return $"{prefix}-{count + 1:D4}";
    }
}
