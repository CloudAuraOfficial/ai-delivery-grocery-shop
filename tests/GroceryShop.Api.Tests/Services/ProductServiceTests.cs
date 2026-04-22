using GroceryShop.Api.Tests.Helpers;
using GroceryShop.Core.DTOs;
using GroceryShop.Infrastructure.Services;

namespace GroceryShop.Api.Tests.Services;

public class ProductServiceTests : IAsyncDisposable
{
    private readonly Infrastructure.Data.GroceryDbContext _db;
    private readonly ProductService _sut;

    public ProductServiceTests()
    {
        // Each test gets a fresh in-memory DB
        _db = TestDbContextFactory.Create();
        _sut = new ProductService(_db);
    }

    public async ValueTask DisposeAsync()
    {
        await _db.DisposeAsync();
    }

    // ─── GetProductsAsync ────────────────────────────────────

    [Fact]
    public async Task GetProducts_ReturnsOnlyAvailableProducts()
    {
        // Arrange
        await TestDbContextFactory.SeedTestDataAsync(_db);

        // Act
        var result = await _sut.GetProductsAsync(page: 1, pageSize: 20);

        // Assert — soft-deleted "Expired Lettuce" (IsAvailable=false) excluded
        Assert.Equal(3, result.TotalCount);
        Assert.DoesNotContain(result.Items, p => p.Name == "Expired Lettuce");
    }

    [Fact]
    public async Task GetProducts_FilterByCategory_ReturnsOnlyCategoryProducts()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsAsync(
            page: 1, pageSize: 20, categoryId: TestData.FreshCategoryId);

        // Apple + Banana (both Fresh), Water (Beverages) excluded
        Assert.Equal(2, result.TotalCount);
        Assert.All(result.Items, p => Assert.Equal(TestData.FreshCategoryId, p.CategoryId));
    }

    [Fact]
    public async Task GetProducts_FilterByOrganic_ReturnsOnlyOrganic()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsAsync(
            page: 1, pageSize: 20, isOrganic: true);

        Assert.Single(result.Items);
        Assert.Equal("Organic Fuji Apple", result.Items[0].Name);
    }

    [Fact]
    public async Task GetProducts_FilterByBrand_CaseInsensitive()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsAsync(
            page: 1, pageSize: 20, brand: "nature");

        Assert.Single(result.Items);
        Assert.Equal("Nature's Best", result.Items[0].Brand);
    }

    [Fact]
    public async Task GetProducts_SortByPriceAsc_ReturnsOrderedResults()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsAsync(
            page: 1, pageSize: 20, sortBy: "price_asc");

        Assert.True(result.Items[0].Price <= result.Items[1].Price);
        Assert.True(result.Items[1].Price <= result.Items[2].Price);
    }

    [Fact]
    public async Task GetProducts_SortByPriceDesc_ReturnsDescendingOrder()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsAsync(
            page: 1, pageSize: 20, sortBy: "price_desc");

        Assert.True(result.Items[0].Price >= result.Items[1].Price);
        Assert.True(result.Items[1].Price >= result.Items[2].Price);
    }

    // ─── Pagination ──────────────────────────────────────────

    [Fact]
    public async Task GetProducts_Pagination_ReturnsCorrectPage()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var page1 = await _sut.GetProductsAsync(page: 1, pageSize: 2);
        var page2 = await _sut.GetProductsAsync(page: 2, pageSize: 2);

        Assert.Equal(2, page1.Items.Count);
        Assert.Single(page2.Items);
        Assert.Equal(3, page1.TotalCount);
        Assert.True(page1.HasNextPage);
        Assert.False(page1.HasPreviousPage);
        Assert.False(page2.HasNextPage);
        Assert.True(page2.HasPreviousPage);
    }

    // ─── GetProductByIdAsync ─────────────────────────────────

    [Fact]
    public async Task GetProductById_ExistingProduct_ReturnsDto()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductByIdAsync(TestData.AppleId);

        Assert.NotNull(result);
        Assert.Equal("Organic Fuji Apple", result.Name);
        Assert.Equal("Fresh", result.CategoryName);
        Assert.Equal("FRE-0001", result.Sku);
    }

    [Fact]
    public async Task GetProductById_IncludesActiveDeal()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductByIdAsync(TestData.AppleId);

        Assert.NotNull(result?.ActiveDeal);
        Assert.Equal("25% Off Organic Apples", result.ActiveDeal.Title);
        Assert.Equal(25m, result.ActiveDeal.DiscountPercent);
    }

    [Fact]
    public async Task GetProductById_NoActiveDeal_ReturnsNullDeal()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductByIdAsync(TestData.WaterId);

        Assert.NotNull(result);
        Assert.Null(result.ActiveDeal);
    }

    [Fact]
    public async Task GetProductById_NonExistent_ReturnsNull()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductByIdAsync(Guid.NewGuid());

        Assert.Null(result);
    }

    // ─── SearchProductsAsync ─────────────────────────────────

    [Fact]
    public async Task SearchProducts_ByName_FindsMatch()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.SearchProductsAsync("apple", 1, 20);

        Assert.Single(result.Items);
        Assert.Equal("Organic Fuji Apple", result.Items[0].Name);
    }

    [Fact]
    public async Task SearchProducts_ByTag_FindsMatch()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.SearchProductsAsync("hydration", 1, 20);

        Assert.Single(result.Items);
        Assert.Equal("Spring Water 24-Pack", result.Items[0].Name);
    }

    [Fact]
    public async Task SearchProducts_ByBrand_FindsMatch()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.SearchProductsAsync("crystal", 1, 20);

        Assert.Single(result.Items);
        Assert.Equal("Spring Water 24-Pack", result.Items[0].Name);
    }

    [Fact]
    public async Task SearchProducts_ExcludesSoftDeleted()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.SearchProductsAsync("lettuce", 1, 20);

        Assert.Empty(result.Items);
    }

    [Fact]
    public async Task SearchProducts_CaseInsensitive()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.SearchProductsAsync("BANANA", 1, 20);

        Assert.Single(result.Items);
    }

    // ─── CreateProductAsync ──────────────────────────────────

    [Fact]
    public async Task CreateProduct_PersistsAndReturnsDto()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var dto = new CreateProductDto(
            CategoryId: TestData.FreshCategoryId,
            Name: "Roma Tomatoes",
            Description: "Vine-ripened roma tomatoes",
            Brand: null,
            Price: 3.49m,
            Unit: "lb",
            Weight: "1 lb",
            ImageUrl: null,
            IsOrganic: false,
            IsStoreBrand: false,
            NutritionInfo: null,
            Tags: "vegetable,tomato"
        );

        var result = await _sut.CreateProductAsync(dto);

        Assert.NotEqual(Guid.Empty, result.Id);
        Assert.Equal("Roma Tomatoes", result.Name);
        Assert.Equal("roma-tomatoes", result.Slug);
        Assert.Equal(3.49m, result.Price);
        Assert.StartsWith("FRE-", result.Sku); // auto-generated from category slug
    }

    // ─── UpdateProductAsync ──────────────────────────────────

    [Fact]
    public async Task UpdateProduct_ExistingProduct_UpdatesFields()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var dto = new CreateProductDto(
            CategoryId: TestData.FreshCategoryId,
            Name: "Organic Gala Apple",
            Description: "Updated description",
            Brand: "Nature's Best",
            Price: 2.49m,
            Unit: "each",
            Weight: null,
            ImageUrl: null,
            IsOrganic: true,
            IsStoreBrand: false,
            NutritionInfo: null,
            Tags: "fruit,organic"
        );

        var result = await _sut.UpdateProductAsync(TestData.AppleId, dto);

        Assert.NotNull(result);
        Assert.Equal("Organic Gala Apple", result.Name);
        Assert.Equal(2.49m, result.Price);
    }

    [Fact]
    public async Task UpdateProduct_NonExistent_ReturnsNull()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var dto = new CreateProductDto(
            TestData.FreshCategoryId, "X", "X", null, 1m, "each",
            null, null, false, false, null, null);

        var result = await _sut.UpdateProductAsync(Guid.NewGuid(), dto);

        Assert.Null(result);
    }

    // ─── DeleteProductAsync (soft delete) ────────────────────

    [Fact]
    public async Task DeleteProduct_SetsIsAvailableFalse()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.DeleteProductAsync(TestData.BananaId);

        Assert.True(result);

        // Verify soft-deleted: no longer in available list
        var products = await _sut.GetProductsAsync(1, 20);
        Assert.DoesNotContain(products.Items, p => p.Id == TestData.BananaId);
    }

    [Fact]
    public async Task DeleteProduct_NonExistent_ReturnsFalse()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.DeleteProductAsync(Guid.NewGuid());

        Assert.False(result);
    }

    // ─── GetProductsByCategorySlugAsync ──────────────────────

    [Fact]
    public async Task GetProductsByCategorySlug_ValidSlug_ReturnsProducts()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsByCategorySlugAsync("fresh", 1, 20);

        Assert.Equal(2, result.TotalCount);
    }

    [Fact]
    public async Task GetProductsByCategorySlug_InvalidSlug_ReturnsEmpty()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsByCategorySlugAsync("nonexistent", 1, 20);

        Assert.Empty(result.Items);
        Assert.Equal(0, result.TotalCount);
    }

    // ─── Interview talking point: DealsOnly filter ───────────

    [Fact]
    public async Task GetProducts_DealsOnlyFilter_ReturnsOnlyProductsWithActiveDeals()
    {
        await TestDbContextFactory.SeedTestDataAsync(_db);

        var result = await _sut.GetProductsAsync(
            page: 1, pageSize: 20, dealsOnly: true);

        // Only the Apple has an active deal
        Assert.Single(result.Items);
        Assert.Equal("Organic Fuji Apple", result.Items[0].Name);
    }
}
