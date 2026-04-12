using GroceryShop.Core.DTOs;

namespace GroceryShop.Core.Interfaces;

public interface IStoreService
{
    Task<IReadOnlyList<StoreDto>> GetAllStoresAsync();
    Task<StoreDto?> GetStoreByIdAsync(Guid id);
    Task<IReadOnlyList<StoreDto>> GetNearbyStoresAsync(decimal latitude, decimal longitude);
}
