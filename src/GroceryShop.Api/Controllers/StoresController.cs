using GroceryShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GroceryShop.Api.Controllers;

[ApiController]
[Route("api/v1/stores")]
public class StoresController : ControllerBase
{
    private readonly IStoreService _storeService;

    public StoresController(IStoreService storeService) => _storeService = storeService;

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var stores = await _storeService.GetAllStoresAsync();
        return Ok(stores);
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var store = await _storeService.GetStoreByIdAsync(id);
        return store == null ? NotFound() : Ok(store);
    }

    [HttpGet("nearby")]
    public async Task<IActionResult> GetNearby([FromQuery] decimal lat, [FromQuery] decimal lng)
    {
        var stores = await _storeService.GetNearbyStoresAsync(lat, lng);
        return Ok(stores);
    }
}
