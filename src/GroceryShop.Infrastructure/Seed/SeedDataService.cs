using GroceryShop.Core.Entities;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace GroceryShop.Infrastructure.Seed;

public class SeedDataService
{
    private readonly GroceryDbContext _db;
    private readonly ILogger<SeedDataService> _logger;

    public SeedDataService(GroceryDbContext db, ILogger<SeedDataService> logger)
    {
        _db = db;
        _logger = logger;
    }

    public async Task SeedAsync()
    {
        await _db.Database.MigrateAsync();

        if (await _db.Categories.AnyAsync())
        {
            _logger.LogInformation("Database already seeded, skipping");
            return;
        }

        _logger.LogInformation("Seeding categories and stores...");

        await SeedCategoriesAsync();
        await SeedStoresAsync();

        _logger.LogInformation("Seed complete");
    }

    private async Task SeedCategoriesAsync()
    {
        var categories = new List<Category>
        {
            new() { Name = "Baby", Slug = "baby", Description = "Diapers, formula, baby food, wipes, and nursery essentials", DisplayOrder = 1 },
            new() { Name = "Beverages", Slug = "beverages", Description = "Water, soda, juice, coffee, tea, and energy drinks", DisplayOrder = 2 },
            new() { Name = "Household", Slug = "household", Description = "Cleaning supplies, paper products, laundry, and home essentials", DisplayOrder = 3 },
            new() { Name = "Fresh", Slug = "fresh", Description = "Fresh fruits, vegetables, herbs, and salads", DisplayOrder = 4 },
            new() { Name = "Meat & Seafood", Slug = "meat-seafood", Description = "Fresh and frozen beef, chicken, pork, fish, and shellfish", DisplayOrder = 5 },
            new() { Name = "Deli", Slug = "deli", Description = "Sliced meats, cheeses, prepared meals, and deli salads", DisplayOrder = 6 },
        };

        _db.Categories.AddRange(categories);
        await _db.SaveChangesAsync();
        _logger.LogInformation("Seeded {Count} categories", categories.Count);
    }

    private async Task SeedStoresAsync()
    {
        var stores = new List<Store>
        {
            new() { Name = "AI Grocery - Lakeland South", StoreNumber = "1001", Address = "3501 S Florida Ave", City = "Lakeland", State = "FL", ZipCode = "33803", Phone = "(863) 555-0101", Latitude = 28.0096m, Longitude = -81.9568m },
            new() { Name = "AI Grocery - Lakeland North", StoreNumber = "1002", Address = "4730 N Socrum Loop Rd", City = "Lakeland", State = "FL", ZipCode = "33809", Phone = "(863) 555-0102", Latitude = 28.0884m, Longitude = -81.9839m },
            new() { Name = "AI Grocery - Winter Haven", StoreNumber = "1003", Address = "200 Cypress Gardens Blvd", City = "Winter Haven", State = "FL", ZipCode = "33880", Phone = "(863) 555-0103", Latitude = 28.0222m, Longitude = -81.7329m },
            new() { Name = "AI Grocery - Plant City", StoreNumber = "1004", Address = "2602 James L Redman Pkwy", City = "Plant City", State = "FL", ZipCode = "33566", Phone = "(813) 555-0104", Latitude = 28.0086m, Longitude = -82.1187m },
            new() { Name = "AI Grocery - Bartow", StoreNumber = "1005", Address = "1050 N Broadway Ave", City = "Bartow", State = "FL", ZipCode = "33830", Phone = "(863) 555-0105", Latitude = 27.9059m, Longitude = -81.8432m },
            new() { Name = "AI Grocery - Auburndale", StoreNumber = "1006", Address = "508 Havendale Blvd", City = "Auburndale", State = "FL", ZipCode = "33823", Phone = "(863) 555-0106", Latitude = 28.0728m, Longitude = -81.8033m },
            new() { Name = "AI Grocery - Haines City", StoreNumber = "1007", Address = "36000 US Hwy 27", City = "Haines City", State = "FL", ZipCode = "33844", Phone = "(863) 555-0107", Latitude = 28.1144m, Longitude = -81.6181m },
            new() { Name = "AI Grocery - Mulberry", StoreNumber = "1008", Address = "901 N Church Ave", City = "Mulberry", State = "FL", ZipCode = "33860", Phone = "(863) 555-0108", Latitude = 27.8986m, Longitude = -81.9748m },
            new() { Name = "AI Grocery - Davenport", StoreNumber = "1009", Address = "2400 Posner Blvd", City = "Davenport", State = "FL", ZipCode = "33837", Phone = "(863) 555-0109", Latitude = 28.1614m, Longitude = -81.6016m },
        };

        _db.Stores.AddRange(stores);
        await _db.SaveChangesAsync();

        // Seed store hours (7am-10pm daily for all stores)
        var storeHours = new List<StoreHours>();
        foreach (var store in stores)
        {
            for (int day = 0; day <= 6; day++)
            {
                storeHours.Add(new StoreHours
                {
                    StoreId = store.Id,
                    DayOfWeek = day,
                    OpenTime = new TimeOnly(7, 0),
                    CloseTime = new TimeOnly(22, 0)
                });
            }
        }

        _db.StoreHours.AddRange(storeHours);
        await _db.SaveChangesAsync();
        _logger.LogInformation("Seeded {StoreCount} stores with {HoursCount} hours entries", stores.Count, storeHours.Count);
    }
}
