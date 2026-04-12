using GroceryShop.Core.DTOs;
using GroceryShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GroceryShop.Api.Controllers;

[ApiController]
[Route("api/v1/cart")]
public class CartController : ControllerBase
{
    private readonly ICartService _cartService;

    public CartController(ICartService cartService) => _cartService = cartService;

    private string GetSessionId() =>
        Request.Headers["X-Session-Id"].FirstOrDefault() ?? "anonymous";

    [HttpGet]
    public async Task<IActionResult> GetCart()
    {
        var cart = await _cartService.GetCartAsync(GetSessionId());
        return Ok(cart);
    }

    [HttpPost("items")]
    public async Task<IActionResult> AddItem([FromBody] AddToCartDto dto)
    {
        var cart = await _cartService.AddItemAsync(GetSessionId(), dto);
        return Ok(cart);
    }

    [HttpPut("items/{productId:guid}")]
    public async Task<IActionResult> UpdateItem(Guid productId, [FromBody] UpdateCartItemDto dto)
    {
        var cart = await _cartService.UpdateItemAsync(GetSessionId(), productId, dto);
        return Ok(cart);
    }

    [HttpDelete("items/{productId:guid}")]
    public async Task<IActionResult> RemoveItem(Guid productId)
    {
        var cart = await _cartService.RemoveItemAsync(GetSessionId(), productId);
        return Ok(cart);
    }

    [HttpDelete]
    public async Task<IActionResult> ClearCart()
    {
        await _cartService.ClearCartAsync(GetSessionId());
        return NoContent();
    }
}
