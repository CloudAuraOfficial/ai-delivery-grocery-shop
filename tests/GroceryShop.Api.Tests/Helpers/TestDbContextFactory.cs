using GroceryShop.Core.Entities;
using GroceryShop.Core.Enums;
using GroceryShop.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace GroceryShop.Api.Tests.Helpers;

public static class TestDbContextFactory
{
    public static GroceryDbContext Create(string? dbName = null)
    {
        var options = new DbContextOptionsBuilder<GroceryDbContext>()
            .UseInMemoryDatabase(dbName ?? Guid.NewGuid().ToString())
            .Options;

        return new GroceryDbContext(options);
    }

    public static async Task<GroceryDbContext> CreateSeededAsync(string? dbName = null)
    {
        var db = Create(dbName);
        await SeedTestDataAsync(db);
        return db;
    }

    public static async Task SeedTestDataAsync(GroceryDbContext db)
    {
        var category = new Category
        {
            Id = TestData.FreshCategoryId,
            Name = "Fresh",
            Slug = "fresh",
            Description = "Fresh produce",
            DisplayOrder = 1,
            IsActive = true
        };

        var category2 = new Category
        {
            Id = TestData.BeveragesCategoryId,
            Name = "Beverages",
            Slug = "beverages",
            Description = "Drinks",
            DisplayOrder = 2,
            IsActive = true
        };

        db.Categories.AddRange(category, category2);

        var products = new List<Product>
        {
            new()
            {
                Id = TestData.AppleId,
                CategoryId = TestData.FreshCategoryId,
                Name = "Organic Fuji Apple",
                Slug = "organic-fuji-apple",
                Description = "Crisp organic Fuji apples",
                Brand = "Nature's Best",
                Price = 1.99m,
                Unit = "each",
                Sku = "FRE-0001",
                IsAvailable = true,
                IsOrganic = true,
                Tags = "fruit,organic,apple"
            },
            new()
            {
                Id = TestData.BananaId,
                CategoryId = TestData.FreshCategoryId,
                Name = "Banana Bundle",
                Slug = "banana-bundle",
                Description = "Yellow bananas, bundle of 5",
                Price = 2.49m,
                Unit = "each",
                Sku = "FRE-0002",
                IsAvailable = true,
                IsOrganic = false,
                Tags = "fruit,banana"
            },
            new()
            {
                Id = TestData.WaterId,
                CategoryId = TestData.BeveragesCategoryId,
                Name = "Spring Water 24-Pack",
                Slug = "spring-water-24-pack",
                Description = "Pure spring water",
                Brand = "Crystal Clear",
                Price = 4.99m,
                Unit = "pack",
                Sku = "BEV-0001",
                IsAvailable = true,
                Tags = "water,hydration"
            },
            new()
            {
                Id = TestData.DeletedProductId,
                CategoryId = TestData.FreshCategoryId,
                Name = "Expired Lettuce",
                Slug = "expired-lettuce",
                Description = "No longer available",
                Price = 1.49m,
                Unit = "each",
                Sku = "FRE-0003",
                IsAvailable = false // soft-deleted
            }
        };

        db.Products.AddRange(products);

        // Active daily deal on apple
        db.Deals.Add(new Deal
        {
            Id = TestData.AppleDealId,
            ProductId = TestData.AppleId,
            DealType = DealType.DailyDeal,
            Title = "25% Off Organic Apples",
            DiscountPercent = 25,
            StartDate = DateTime.UtcNow.AddDays(-1),
            EndDate = DateTime.UtcNow.AddDays(1),
            IsActive = true
        });

        // Expired deal (should not appear)
        db.Deals.Add(new Deal
        {
            Id = Guid.NewGuid(),
            ProductId = TestData.BananaId,
            DealType = DealType.WeeklyDeal,
            Title = "Old Banana Deal",
            DiscountPercent = 10,
            StartDate = DateTime.UtcNow.AddDays(-10),
            EndDate = DateTime.UtcNow.AddDays(-1),
            IsActive = false
        });

        var store = new Store
        {
            Id = TestData.StoreId,
            Name = "AI Grocery - Lakeland South",
            StoreNumber = "1001",
            Address = "3501 S Florida Ave",
            City = "Lakeland",
            State = "FL",
            ZipCode = "33803",
            Phone = "(863) 555-0101",
            Latitude = 28.0096m,
            Longitude = -81.9568m,
            IsOpen = true
        };

        db.Stores.Add(store);

        var user = new User
        {
            Id = TestData.UserId,
            Email = "test@example.com",
            DisplayName = "Test User",
            PasswordHash = "hashed",
            PreferredStoreId = TestData.StoreId
        };

        db.Users.Add(user);
        await db.SaveChangesAsync();
    }
}

public static class TestData
{
    public static readonly Guid FreshCategoryId = Guid.Parse("11111111-1111-1111-1111-111111111111");
    public static readonly Guid BeveragesCategoryId = Guid.Parse("22222222-2222-2222-2222-222222222222");
    public static readonly Guid AppleId = Guid.Parse("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    public static readonly Guid BananaId = Guid.Parse("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    public static readonly Guid WaterId = Guid.Parse("cccccccc-cccc-cccc-cccc-cccccccccccc");
    public static readonly Guid DeletedProductId = Guid.Parse("dddddddd-dddd-dddd-dddd-dddddddddddd");
    public static readonly Guid AppleDealId = Guid.Parse("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee");
    public static readonly Guid StoreId = Guid.Parse("ffffffff-ffff-ffff-ffff-ffffffffffff");
    public static readonly Guid UserId = Guid.Parse("00000000-0000-0000-0000-000000000001");
}
