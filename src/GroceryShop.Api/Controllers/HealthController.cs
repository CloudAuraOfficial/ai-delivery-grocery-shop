using GroceryShop.Infrastructure.Data;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Api.Controllers;

[ApiController]
public class HealthController : ControllerBase
{
    private readonly GroceryDbContext _db;

    public HealthController(GroceryDbContext db) => _db = db;

    [HttpGet("health")]
    public async Task<IActionResult> Health()
    {
        try
        {
            await _db.Database.CanConnectAsync();
            return Ok(new
            {
                status = "healthy",
                timestamp = DateTime.UtcNow,
                database = "connected"
            });
        }
        catch (Exception ex)
        {
            return StatusCode(503, new
            {
                status = "unhealthy",
                timestamp = DateTime.UtcNow,
                database = "disconnected",
                error = ex.Message
            });
        }
    }
}
