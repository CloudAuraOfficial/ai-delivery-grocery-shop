using GroceryShop.Core.DTOs;
using GroceryShop.Core.Enums;
using GroceryShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace GroceryShop.Api.Controllers;

[ApiController]
[Route("api/v1/orders")]
public class OrdersController : ControllerBase
{
    private readonly IOrderService _orderService;

    public OrdersController(IOrderService orderService) => _orderService = orderService;

    [HttpGet]
    public async Task<IActionResult> GetAll([FromQuery] int page = 1, [FromQuery] int pageSize = 20)
    {
        // In production, userId would come from JWT claims
        var userId = GetUserId();
        var result = await _orderService.GetOrdersAsync(userId, page, pageSize);
        return Ok(result);
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var order = await _orderService.GetOrderByIdAsync(id);
        return order == null ? NotFound() : Ok(order);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateOrderDto dto)
    {
        var userId = GetUserId();
        var sessionId = Request.Headers["X-Session-Id"].FirstOrDefault() ?? "anonymous";
        var order = await _orderService.CreateOrderAsync(userId, sessionId, dto);
        return CreatedAtAction(nameof(GetById), new { id = order.Id }, order);
    }

    [HttpPatch("{id:guid}/status")]
    public async Task<IActionResult> UpdateStatus(Guid id, [FromBody] UpdateOrderStatusDto dto)
    {
        var order = await _orderService.UpdateOrderStatusAsync(id, dto.Status);
        return order == null ? NotFound() : Ok(order);
    }

    private Guid GetUserId()
    {
        // Placeholder: in production, extract from JWT claims
        var header = Request.Headers["X-User-Id"].FirstOrDefault();
        return Guid.TryParse(header, out var id) ? id : Guid.Empty;
    }
}

public record UpdateOrderStatusDto(OrderStatus Status);
