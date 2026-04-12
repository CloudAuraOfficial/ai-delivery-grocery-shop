using GroceryShop.Core.DTOs;
using GroceryShop.Core.Enums;
using GroceryShop.Core.Models;

namespace GroceryShop.Core.Interfaces;

public interface IDealService
{
    Task<PagedResult<DealDto>> GetDealsAsync(DealType? type, int page, int pageSize);
    Task<DealDto?> GetDealByIdAsync(Guid id);
    Task<IReadOnlyList<DealDto>> GetBogoDealsAsync();
    Task<IReadOnlyList<DealDto>> GetWeeklyDealsAsync();
    Task<IReadOnlyList<DealDto>> GetDailyDealsAsync();
    Task<DealDto> CreateDealAsync(CreateDealDto dto);
    Task<DealDto?> UpdateDealAsync(Guid id, CreateDealDto dto);
}
