using GroceryShop.Core.DTOs;
using GroceryShop.Core.Entities;
using GroceryShop.Core.Enums;
using GroceryShop.Core.Interfaces;
using GroceryShop.Core.Models;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Infrastructure.Services;

public class DealService : IDealService
{
    private readonly GroceryDbContext _db;

    public DealService(GroceryDbContext db) => _db = db;

    public async Task<PagedResult<DealDto>> GetDealsAsync(DealType? type, int page, int pageSize)
    {
        var query = _db.Deals
            .Include(d => d.Product).ThenInclude(p => p.Category)
            .Where(d => d.IsActive && d.EndDate > DateTime.UtcNow)
            .AsQueryable();

        if (type.HasValue)
            query = query.Where(d => d.DealType == type.Value);

        var totalCount = await query.CountAsync();
        var items = await query
            .OrderBy(d => d.EndDate)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(d => MapToDto(d))
            .ToListAsync();

        return new PagedResult<DealDto> { Items = items, TotalCount = totalCount, Page = page, PageSize = pageSize };
    }

    public async Task<DealDto?> GetDealByIdAsync(Guid id)
    {
        return await _db.Deals
            .Include(d => d.Product).ThenInclude(p => p.Category)
            .Where(d => d.Id == id)
            .Select(d => MapToDto(d))
            .FirstOrDefaultAsync();
    }

    public async Task<IReadOnlyList<DealDto>> GetBogoDealsAsync() => await GetDealsByTypeAsync(DealType.BOGO);
    public async Task<IReadOnlyList<DealDto>> GetWeeklyDealsAsync() => await GetDealsByTypeAsync(DealType.WeeklyDeal);
    public async Task<IReadOnlyList<DealDto>> GetDailyDealsAsync() => await GetDealsByTypeAsync(DealType.DailyDeal);

    public async Task<DealDto> CreateDealAsync(CreateDealDto dto)
    {
        var deal = new Deal
        {
            ProductId = dto.ProductId,
            DealType = dto.DealType,
            Title = dto.Title,
            Description = dto.Description,
            DiscountPercent = dto.DiscountPercent,
            DiscountAmount = dto.DiscountAmount,
            BuyQuantity = dto.BuyQuantity,
            GetQuantity = dto.GetQuantity,
            StartDate = dto.StartDate,
            EndDate = dto.EndDate
        };

        _db.Deals.Add(deal);
        await _db.SaveChangesAsync();
        return (await GetDealByIdAsync(deal.Id))!;
    }

    public async Task<DealDto?> UpdateDealAsync(Guid id, CreateDealDto dto)
    {
        var deal = await _db.Deals.FindAsync(id);
        if (deal == null) return null;

        deal.ProductId = dto.ProductId;
        deal.DealType = dto.DealType;
        deal.Title = dto.Title;
        deal.Description = dto.Description;
        deal.DiscountPercent = dto.DiscountPercent;
        deal.DiscountAmount = dto.DiscountAmount;
        deal.BuyQuantity = dto.BuyQuantity;
        deal.GetQuantity = dto.GetQuantity;
        deal.StartDate = dto.StartDate;
        deal.EndDate = dto.EndDate;

        await _db.SaveChangesAsync();
        return await GetDealByIdAsync(id);
    }

    private async Task<IReadOnlyList<DealDto>> GetDealsByTypeAsync(DealType type)
    {
        return await _db.Deals
            .Include(d => d.Product).ThenInclude(p => p.Category)
            .Where(d => d.IsActive && d.DealType == type && d.EndDate > DateTime.UtcNow)
            .OrderBy(d => d.EndDate)
            .Select(d => MapToDto(d))
            .ToListAsync();
    }

    private static DealDto MapToDto(Deal d) => new(
        d.Id, d.ProductId, d.Product.Name, d.Product.Price, d.Product.ImageUrl,
        d.Product.Category.Name, d.DealType, d.Title, d.Description,
        d.DiscountPercent, d.DiscountAmount, d.BuyQuantity, d.GetQuantity,
        d.StartDate, d.EndDate, d.IsActive
    );
}
