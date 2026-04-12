using GroceryShop.Core.Entities;
using GroceryShop.Core.Enums;
using GroceryShop.Infrastructure.Data;
using Microsoft.Azure.Functions.Worker;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace GroceryShop.Functions;

public class DealRotationFunction
{
    private readonly GroceryDbContext _db;
    private readonly ILogger<DealRotationFunction> _logger;

    public DealRotationFunction(GroceryDbContext db, ILogger<DealRotationFunction> logger)
    {
        _db = db;
        _logger = logger;
    }

    [Function("DealRotation")]
    public async Task Run([TimerTrigger("0 0 5 * * *")] TimerInfo timer)
    {
        _logger.LogInformation("Deal rotation started at {Time}", DateTime.UtcNow);

        // Deactivate expired daily deals
        var expiredDeals = await _db.Deals
            .Where(d => d.DealType == DealType.DailyDeal && d.EndDate < DateTime.UtcNow && d.IsActive)
            .ToListAsync();

        foreach (var deal in expiredDeals)
            deal.IsActive = false;

        _logger.LogInformation("Deactivated {Count} expired daily deals", expiredDeals.Count);

        // Select new daily deals (10-15 random products not already on a deal)
        var existingDealProductIds = await _db.Deals
            .Where(d => d.IsActive && d.EndDate > DateTime.UtcNow)
            .Select(d => d.ProductId)
            .ToListAsync();

        var eligibleProducts = await _db.Products
            .Where(p => p.IsAvailable && !existingDealProductIds.Contains(p.Id))
            .OrderBy(p => Guid.NewGuid())
            .Take(15)
            .ToListAsync();

        var now = DateTime.UtcNow;
        var endOfDay = now.Date.AddDays(1).AddHours(5); // 5 AM UTC = midnight ET

        var newDeals = new List<Deal>();
        var random = new Random();
        foreach (var product in eligibleProducts)
        {
            var pct = random.Next(5) switch
            {
                0 => 25, 1 => 30, 2 => 35, 3 => 40, _ => 50
            };

            newDeals.Add(new Deal
            {
                ProductId = product.Id,
                DealType = DealType.DailyDeal,
                Title = $"Today Only: {pct}% Off",
                Description = $"Flash deal! Save {pct}% on {product.Name} today only.",
                DiscountPercent = pct,
                StartDate = now,
                EndDate = endOfDay,
            });
        }

        _db.Deals.AddRange(newDeals);
        await _db.SaveChangesAsync();

        _logger.LogInformation("Created {Count} new daily deals", newDeals.Count);

        // Trigger AI service reindex via HTTP (fire-and-forget)
        var aiServiceUrl = Environment.GetEnvironmentVariable("AI_SERVICE_URL");
        if (!string.IsNullOrEmpty(aiServiceUrl))
        {
            try
            {
                using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(10) };
                await http.PostAsync($"{aiServiceUrl}/api/embeddings/reindex", null);
                _logger.LogInformation("Triggered deal reindex on AI service");
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to trigger AI reindex");
            }
        }

        _logger.LogInformation("Deal rotation complete. Next: {Next}", timer.ScheduleStatus?.Next);
    }
}
