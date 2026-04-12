using GroceryShop.Core.DTOs;
using GroceryShop.Core.Entities;
using GroceryShop.Core.Interfaces;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Infrastructure.Services;

public class StoreService : IStoreService
{
    private static readonly string[] DayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    private readonly GroceryDbContext _db;

    public StoreService(GroceryDbContext db) => _db = db;

    public async Task<IReadOnlyList<StoreDto>> GetAllStoresAsync()
    {
        return await _db.Stores
            .Include(s => s.Hours)
            .Where(s => s.IsOpen)
            .OrderBy(s => s.StoreNumber)
            .Select(s => MapToDto(s))
            .ToListAsync();
    }

    public async Task<StoreDto?> GetStoreByIdAsync(Guid id)
    {
        return await _db.Stores
            .Include(s => s.Hours)
            .Where(s => s.Id == id)
            .Select(s => MapToDto(s))
            .FirstOrDefaultAsync();
    }

    public async Task<IReadOnlyList<StoreDto>> GetNearbyStoresAsync(decimal latitude, decimal longitude)
    {
        // Simple distance approximation (good enough for nearby stores in same region)
        var stores = await _db.Stores
            .Include(s => s.Hours)
            .Where(s => s.IsOpen)
            .ToListAsync();

        return stores
            .OrderBy(s => Math.Abs((double)(s.Latitude - latitude)) + Math.Abs((double)(s.Longitude - longitude)))
            .Select(s => MapToDto(s))
            .ToList();
    }

    private static StoreDto MapToDto(Store s) => new(
        s.Id, s.Name, s.StoreNumber, s.Address, s.City, s.State, s.ZipCode,
        s.Phone, s.Latitude, s.Longitude, s.IsOpen,
        s.Hours.OrderBy(h => h.DayOfWeek).Select(h => new StoreHoursDto(
            h.DayOfWeek,
            DayNames[h.DayOfWeek],
            h.OpenTime.ToString("h:mm tt"),
            h.CloseTime.ToString("h:mm tt")
        )).ToList()
    );
}
