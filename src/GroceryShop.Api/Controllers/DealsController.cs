using GroceryShop.Core.DTOs;
using GroceryShop.Core.Enums;
using GroceryShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GroceryShop.Api.Controllers;

[ApiController]
[Route("api/v1/deals")]
public class DealsController : ControllerBase
{
    private readonly IDealService _dealService;

    public DealsController(IDealService dealService) => _dealService = dealService;

    [HttpGet]
    public async Task<IActionResult> GetAll([FromQuery] DealType? type = null, [FromQuery] int page = 1, [FromQuery] int pageSize = 20)
    {
        var result = await _dealService.GetDealsAsync(type, page, pageSize);
        return Ok(result);
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var deal = await _dealService.GetDealByIdAsync(id);
        return deal == null ? NotFound() : Ok(deal);
    }

    [HttpGet("bogo")]
    public async Task<IActionResult> GetBogo()
    {
        var deals = await _dealService.GetBogoDealsAsync();
        return Ok(deals);
    }

    [HttpGet("weekly")]
    public async Task<IActionResult> GetWeekly()
    {
        var deals = await _dealService.GetWeeklyDealsAsync();
        return Ok(deals);
    }

    [HttpGet("daily")]
    public async Task<IActionResult> GetDaily()
    {
        var deals = await _dealService.GetDailyDealsAsync();
        return Ok(deals);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateDealDto dto)
    {
        var deal = await _dealService.CreateDealAsync(dto);
        return CreatedAtAction(nameof(GetById), new { id = deal.Id }, deal);
    }

    [HttpPut("{id:guid}")]
    public async Task<IActionResult> Update(Guid id, [FromBody] CreateDealDto dto)
    {
        var deal = await _dealService.UpdateDealAsync(id, dto);
        return deal == null ? NotFound() : Ok(deal);
    }
}
