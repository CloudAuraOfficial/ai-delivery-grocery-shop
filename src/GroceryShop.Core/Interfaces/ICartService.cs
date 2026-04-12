using GroceryShop.Core.DTOs;

namespace GroceryShop.Core.Interfaces;

public interface ICartService
{
    Task<CartDto> GetCartAsync(string sessionId);
    Task<CartDto> AddItemAsync(string sessionId, AddToCartDto dto);
    Task<CartDto> UpdateItemAsync(string sessionId, Guid productId, UpdateCartItemDto dto);
    Task<CartDto> RemoveItemAsync(string sessionId, Guid productId);
    Task ClearCartAsync(string sessionId);
}
